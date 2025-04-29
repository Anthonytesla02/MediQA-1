"""
Authentication Module for MediQA

This module handles user authentication, including login, signup, and session management.
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from models import User
from gamification import update_user_streak

# Configure logging
logger = logging.getLogger(__name__)

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/user/signup', methods=['POST'])
def signup():
    """Handle user signup requests."""
    try:
        # Get data from request
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
            
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validate input
        if not username or not email or not password:
            return jsonify({"error": "Username, email, and password are required"}), 400
            
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            if existing_user.username == username:
                return jsonify({"error": "Username already taken"}), 400
            else:
                return jsonify({"error": "Email already registered"}), 400
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            points=0,
            streak=0,
            last_active=datetime.utcnow()
        )
        
        # Save to database
        db.session.add(user)
        db.session.commit()
        
        # Log the user in
        login_user(user)
        
        # For compatibility with existing code
        session['user_id'] = user.id
        
        # Return success response
        return jsonify({
            "success": True,
            "message": "Account created successfully!",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "points": user.points,
                "streak": user.streak
            }
        })
    except Exception as e:
        logger.error(f"Error in signup: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "An error occurred during signup"}), 500

@auth_bp.route('/api/user/login', methods=['POST'])
def login():
    """Handle user login requests."""
    try:
        # Get data from request
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
            
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validate input
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        # Check if user exists and password is correct
        if not user or not check_password_hash(user.password_hash, password):
            logger.info(f"Failed login attempt for email: {email}")
            return jsonify({"error": "Invalid email or password"}), 401
        
        # Log the user in
        login_user(user)
        
        # For compatibility with existing code
        session['user_id'] = user.id
        
        # Update user streak
        update_user_streak(user.id)
        
        # Return success response
        return jsonify({
            "success": True,
            "message": "Logged in successfully!",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "points": user.points,
                "streak": user.streak
            }
        })
    except Exception as e:
        logger.error(f"Error in login: {str(e)}")
        return jsonify({"error": "An error occurred during login"}), 500

@auth_bp.route('/api/user/logout', methods=['POST'])
def logout():
    """Handle user logout requests."""
    try:
        # Log the user out
        logout_user()
        
        # Clear session data
        session.pop('user_id', None)
        session.clear()
        
        return jsonify({
            "success": True,
            "message": "Logged out successfully!"
        })
    except Exception as e:
        logger.error(f"Error in logout: {str(e)}")
        return jsonify({"error": "An error occurred during logout"}), 500

@auth_bp.route('/api/user/validate', methods=['GET'])
def validate_session():
    """Validate if user session is still active."""
    try:
        if current_user.is_authenticated:
            return jsonify({
                "valid": True,
                "user": {
                    "id": current_user.id,
                    "username": current_user.username,
                    "points": current_user.points,
                    "streak": current_user.streak
                }
            })
        else:
            return jsonify({
                "valid": False,
                "error": "No active session"
            }), 401
    except Exception as e:
        logger.error(f"Error validating session: {str(e)}")
        return jsonify({
            "valid": False,
            "error": "Session validation error"
        }), 500