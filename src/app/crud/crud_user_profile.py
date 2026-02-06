"""
GUTTERS CRUD for UserProfile

Database operations for user cosmic profiles.
"""
from fastcrud import FastCRUD

from ..models.user_profile import UserProfile

# Create CRUD instance
crud_user_profiles = FastCRUD(UserProfile)
