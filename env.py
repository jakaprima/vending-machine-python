# Add this import statement at the top of the file
from models import Base  # Import your SQLAlchemy Base object containing your models

# Add this line inside the `run_migrations_online` function before `context.run_migrations()`
target_metadata = Base.metadata
