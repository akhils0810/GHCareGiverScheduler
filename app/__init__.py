from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize SQLAlchemy
db = SQLAlchemy()

def create_app():
    try:
        logger.debug("Starting application creation...")
        app = Flask(__name__)
        
        # Load configuration
        from .config import Config, ShiftConfig
        app.config.from_object(Config)
        
        # Ensure instance directory exists
        os.makedirs(os.path.join(app.root_path, '..', 'instance'), exist_ok=True)
        
        # Initialize database
        db.init_app(app)
        
        # Import models here to avoid circular imports
        from .models import Caregiver, Shift
        
        with app.app_context():
            logger.debug("Creating database tables...")
            
            # In Render environment, drop all tables and recreate
            if os.environ.get('RENDER'):
                logger.debug("Render environment detected - dropping all tables")
                db.drop_all()
                logger.debug("Tables dropped successfully")
            
            db.create_all()
            logger.debug("Tables created successfully")
            
            # Initialize caregivers if none exist
            if Caregiver.query.count() == 0:
                logger.debug("Initializing caregivers...")
                for name in ShiftConfig.CAREGIVERS:
                    caregiver = Caregiver(name=name)
                    db.session.add(caregiver)
                db.session.commit()
                logger.debug(f"Added {len(ShiftConfig.CAREGIVERS)} caregivers")
                
                # Add initial schedule
                logger.debug("Adding initial schedule...")
                # Get all caregivers
                caregivers = {c.name: c for c in Caregiver.query.all()}
                logger.debug(f"Found caregivers: {list(caregivers.keys())}")
                
                # Get the Monday of current week
                today = datetime.now().date()
                monday = today - timedelta(days=today.weekday())
                
                # Initial schedule data
                schedule = {
                    'Monday': {
                        'A': 'Maria B',
                        'G1': 'Teontae',
                        'B': 'Amanda',
                        'C': 'Michelle'
                    },
                    'Tuesday': {
                        'A': 'Fatima',
                        'G1': 'Mariah G',
                        'B': 'Kisha',
                        'C': 'Michelle'
                    },
                    'Wednesday': {
                        'A': 'Maria B',
                        'G1': 'Mariah G',
                        'B': 'Kisha',
                        'C': 'Amanda'
                    },
                    'Thursday': {
                        'A': 'Fatima',
                        'G1': 'Maria B',
                        'B': 'Kisha',
                        'C': 'Amanda'
                    },
                    'Friday': {
                        'A': 'Maria B',
                        'G1': 'Fatima',
                        'B': 'Kisha',
                        'C': 'Amanda'
                    },
                    'Saturday': {
                        'A': 'Mariah G',
                        'G2': 'Teontae',
                        'G1': 'Fatima',
                        'B': 'Michelle',
                        'C': 'Kisha'
                    },
                    'Sunday': {
                        'A': 'Mariah G',
                        'G2': 'Teontae',
                        'G1': 'Fatima',
                        'B': 'Michelle',
                        'C': 'Amanda'
                    }
                }
                
                # Add shifts to database
                days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                for i, day in enumerate(days):
                    date = monday + timedelta(days=i)
                    logger.debug(f"Adding shifts for {day}")
                    for shift_type, caregiver_name in schedule[day].items():
                        if caregiver_name in caregivers:
                            shift = Shift(
                                date=date,
                                shift_type=shift_type,
                                caregiver_id=caregivers[caregiver_name].id
                            )
                            db.session.add(shift)
                            logger.debug(f"Added shift: {day} - {shift_type} - {caregiver_name}")
                        else:
                            logger.warning(f"Caregiver {caregiver_name} not found in database")
                
                db.session.commit()
                logger.debug("Initial schedule added successfully")
            else:
                logger.debug(f"Found {Caregiver.query.count()} existing caregivers, skipping initialization")
        
        # Register blueprints
        from .routes import views
        app.register_blueprint(views)
        
        logger.debug("Application creation completed successfully")
        return app
    except Exception as e:
        logger.error(f"Error creating application: {str(e)}")
        raise

# Create the application instance
app = create_app() 