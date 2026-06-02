from pydantic import BaseModel


class UserCreate(BaseModel):
    """Basic user schema for future signup work.

    Authentication is intentionally not implemented in Stage 4 MVP v1.
    """

    name: str
    email: str
    password: str


class UserResponse(BaseModel):
    """Public user data returned by future user APIs."""

    name: str
    email: str
