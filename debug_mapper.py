import sys

from sqlalchemy.orm import configure_mappers

# Add src to path
sys.path.append("src")

from src.app.models.user import User


def test_mappers():
    print("Checking User attributes...")
    if "chat_sessions" in dir(User):
        print("User has chat_sessions attribute")
    else:
        print("User does NOT have chat_sessions attribute")

    print("Configuring mappers...")
    try:
        configure_mappers()
        print("Mappers configured successfully!")
    except Exception as e:
        print(f"Error configuring mappers: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_mappers()
