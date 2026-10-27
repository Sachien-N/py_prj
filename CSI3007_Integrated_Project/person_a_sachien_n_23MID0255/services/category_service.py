"""Configurable expense categories and rule-based keyword matching."""

from __future__ import annotations

import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from errors import AppError
from models import Budget, Category, Expense
from schemas import CategoryCreate, CategoryUpdate

DEFAULT_CATEGORIES = [
    {
        "name": "Food",
        "description": "Meals, groceries, restaurants and food delivery",
        "keywords": [
            "restaurant",
            "cafe",
            "coffee",
            "grocery",
            "groceries",
            "swiggy",
            "zomato",
            "bigbasket",
            "food",
            "bakery",
        ],
        "color": "#ea580c",
        "priority": 80,
    },
    {
        "name": "Transport",
        "description": "Local travel, fuel, parking and public transport",
        "keywords": [
            "uber",
            "ola",
            "auto",
            "cab",
            "petrol",
            "diesel",
            "fuel",
            "metro",
            "bus",
            "train",
            "parking",
        ],
        "color": "#0284c7",
        "priority": 80,
    },
    {
        "name": "Shopping",
        "description": "Clothing, electronics and general shopping",
        "keywords": [
            "amazon",
            "flipkart",
            "myntra",
            "shopping",
            "clothing",
            "mall",
            "store",
            "electronics",
        ],
        "color": "#7c3aed",
        "priority": 70,
    },
    {
        "name": "Education",
        "description": "Courses, books, tuition and academic fees",
        "keywords": [
            "course",
            "udemy",
            "coursera",
            "tuition",
            "book",
            "school",
            "college",
            "exam",
            "education",
        ],
        "color": "#2563eb",
        "priority": 70,
    },
    {
        "name": "Entertainment",
        "description": "Streaming, events, games and leisure",
        "keywords": [
            "netflix",
            "spotify",
            "prime video",
            "hotstar",
            "movie",
            "cinema",
            "game",
            "concert",
            "entertainment",
        ],
        "color": "#db2777",
        "priority": 70,
    },
    {
        "name": "Utilities",
        "description": "Electricity, water, gas, internet and phone bills",
        "keywords": [
            "electricity",
            "tneb",
            "tangedco",
            "water",
            "gas",
            "broadband",
            "internet",
            "recharge",
            "mobile",
            "utility",
            "bill",
        ],
        "color": "#ca8a04",
        "priority": 90,
    },
    {
        "name": "Healthcare",
        "description": "Medical care, medicines and health services",
        "keywords": [
            "pharmacy",
            "hospital",
            "doctor",
            "clinic",
            "medical",
            "medicine",
            "apollo",
            "health",
        ],
        "color": "#dc2626",
        "priority": 80,
    },
    {
        "name": "Miscellaneous",
        "description": "Uncategorised or other personal spending",
        "keywords": [],
        "color": "#64748b",
        "priority": 1,
    },
]


def seed_default_categories(db: Session) -> None:
    existing = {name.lower() for name in db.scalars(select(Category.name)).all()}
    for item in DEFAULT_CATEGORIES:
        if item["name"].lower() not in existing:
            db.add(
                Category(
                    name=item["name"],
                    description=item["description"],
                    keywords=json.dumps(item["keywords"]),
                    color=item["color"],
                    priority=item["priority"],
                )
            )
    db.commit()


def serialize_category(category: Category) -> dict:
    return {
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "keywords": category.keyword_list,
        "color": category.color,
        "priority": category.priority,
        "is_active": category.is_active,
        "created_at": category.created_at,
    }


def list_categories(db: Session, include_inactive: bool = False) -> list[Category]:
    stmt = select(Category).order_by(Category.priority.desc(), Category.name)
    if not include_inactive:
        stmt = stmt.where(Category.is_active.is_(True))
    return list(db.scalars(stmt).all())


def find_category(db: Session, name: str) -> Category | None:
    return db.scalar(select(Category).where(func.lower(Category.name) == name.strip().lower()))


def require_category(db: Session, name: str) -> Category:
    category = find_category(db, name)
    if not category or not category.is_active:
        raise AppError(f"Unknown or inactive category: {name}", status_code=422)
    return category


def get_or_create_external_category(db: Session, name: str) -> Category:
    category = find_category(db, name)
    if category:
        return category
    category = Category(
        name=name.strip()[:60],
        description="Category supplied by an external application",
        keywords="[]",
        color="#64748b",
        priority=10,
    )
    db.add(category)
    db.flush()
    return category


def create_category(db: Session, payload: CategoryCreate) -> Category:
    if find_category(db, payload.name):
        raise AppError("A category with that name already exists", status_code=409)
    category = Category(
        name=payload.name,
        description=payload.description,
        keywords=json.dumps(payload.keywords),
        color=payload.color.lower(),
        priority=payload.priority,
        is_active=payload.is_active,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category_id: int, payload: CategoryUpdate) -> Category:
    category = db.get(Category, category_id)
    if not category:
        raise AppError("Category not found", status_code=404)
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"]:
        duplicate = find_category(db, data["name"])
        if duplicate and duplicate.id != category.id:
            raise AppError("A category with that name already exists", status_code=409)
        category.name = data["name"]
    if "description" in data and data["description"] is not None:
        category.description = data["description"]
    if "keywords" in data and data["keywords"] is not None:
        category.keywords = json.dumps(data["keywords"])
    if "color" in data and data["color"]:
        category.color = data["color"].lower()
    if "priority" in data and data["priority"] is not None:
        category.priority = data["priority"]
    if "is_active" in data and data["is_active"] is not None:
        if not data["is_active"] and _category_in_use(db, category.id):
            raise AppError(
                "This category is referenced by expenses or budgets; deactivate is blocked",
                status_code=409,
            )
        category.is_active = data["is_active"]
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> None:
    category = db.get(Category, category_id)
    if not category:
        raise AppError("Category not found", status_code=404)
    if _category_in_use(db, category.id):
        raise AppError(
            "Category cannot be deleted while expenses or budgets reference it",
            status_code=409,
        )
    db.delete(category)
    db.commit()


def _category_in_use(db: Session, category_id: int) -> bool:
    expense_count = db.scalar(
        select(func.count(Expense.id)).where(Expense.category_id == category_id)
    )
    budget_count = db.scalar(
        select(func.count(Budget.id)).where(Budget.category_id == category_id)
    )
    return bool(expense_count or budget_count)


def categorize_merchant(db: Session, merchant: str, description: str = "") -> Category:
    """Pick the best keyword match. Longest keyword wins, then priority, then name."""
    text = f"{merchant} {description}".lower()
    best: tuple[int, int, str, Category] | None = None
    for category in list_categories(db):
        for keyword in category.keyword_list:
            if keyword and keyword in text:
                score = (len(keyword), category.priority, category.name.lower(), category)
                if best is None or score[:3] > best[:3]:
                    best = score
    if best:
        return best[3]
    fallback = find_category(db, "Miscellaneous")
    if fallback:
        return fallback
    fallback = Category(
        name="Miscellaneous",
        description="Uncategorised spending",
        keywords="[]",
        color="#64748b",
        priority=1,
    )
    db.add(fallback)
    db.flush()
    return fallback
