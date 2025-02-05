"""
Timeline management module for Fiction Timelines application.
Handles creation, modification, and management of fictional timelines and their events.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Set
from enum import Enum
import json

class TimelineError(Exception):
    """Base exception class for Timeline-related errors"""
    pass

class EventConflictError(TimelineError):
    """Raised when there's a conflict between events"""
    pass

class PermissionError(TimelineError):
    """Raised when a user doesn't have required permissions"""
    pass

class Permission(Enum):
    """Enumeration of possible timeline permissions"""
    VIEW = "view"
    EDIT = "edit"
    ADMIN = "admin"

@dataclass
class Event:
    """Represents a single event in the timeline"""
    id: str
    title: str
    description: str
    date: str  # Store as string to support arbitrary dating systems
    categories: Set[str] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)
    created_by: str = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    modified_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        """Convert event to dictionary for serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'date': self.date,
            'categories': list(self.categories),
            'tags': list(self.tags),
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat()
        }

@dataclass
class Timeline:
    """Main Timeline class for managing fictional timelines"""
    id: str
    title: str
    description: str
    dating_system: str
    events: List[Event] = field(default_factory=list)
    owner_id: str = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    modified_at: datetime = field(default_factory=datetime.utcnow)
    collaborators: Dict[str, Permission] = field(default_factory=dict)
    parent_timeline_id: Optional[str] = None
    
    def add_event(self, event: Event, user_id: str) -> None:
        """
        Add a new event to the timeline
        
        Args:
            event: Event object to add
            user_id: ID of user adding the event
            
        Raises:
            PermissionError: If user doesn't have edit permissions
            EventConflictError: If event conflicts with existing events
        """
        if not self._can_edit(user_id):
            raise PermissionError("User does not have permission to add events")
            
        if self._check_conflicts(event):
            raise EventConflictError("Event conflicts with existing events")
            
        event.created_by = user_id
        self.events.append(event)
        self.modified_at = datetime.utcnow()
    
    def edit_event(self, event_id: str, updated_event: Event, user_id: str) -> None:
        """
        Edit an existing event
        
        Args:
            event_id: ID of event to edit
            updated_event: New event data
            user_id: ID of user making the edit
            
        Raises:
            PermissionError: If user doesn't have edit permissions
            EventConflictError: If updated event conflicts with existing events
        """
        if not self._can_edit(user_id):
            raise PermissionError("User does not have permission to edit events")
            
        for i, event in enumerate(self.events):
            if event.id == event_id:
                if self._check_conflicts(updated_event, exclude_id=event_id):
                    raise EventConflictError("Updated event conflicts with existing events")
                    
                updated_event.modified_at = datetime.utcnow()
                self.events[i] = updated_event
                self.modified_at = datetime.utcnow()
                return
                
        raise TimelineError(f"Event with id {event_id} not found")
    
    def delete_event(self, event_id: str, user_id: str) -> None:
        """
        Delete an event from the timeline
        
        Args:
            event_id: ID of event to delete
            user_id: ID of user requesting deletion
            
        Raises:
            PermissionError: If user doesn't have edit permissions
        """
        if not self._can_edit(user_id):
            raise PermissionError("User does not have permission to delete events")
            
        self.events = [e for e in self.events if e.id != event_id]
        self.modified_at = datetime.utcnow()
    
    def add_collaborator(self, user_id: str, permission: Permission, admin_id: str) -> None:
        """
        Add a collaborator to the timeline
        
        Args:
            user_id: ID of user to add as collaborator
            permission: Permission level to grant
            admin_id: ID of user granting permission
            
        Raises:
            PermissionError: If admin_id doesn't have admin permissions
        """
        if not self._is_admin(admin_id):
            raise PermissionError("Only admins can add collaborators")
            
        self.collaborators[user_id] = permission
        self.modified_at = datetime.utcnow()
    
    def remove_collaborator(self, user_id: str, admin_id: str) -> None:
        """
        Remove a collaborator from the timeline
        
        Args:
            user_id: ID of user to remove
            admin_id: ID of user removing collaborator
            
        Raises:
            PermissionError: If admin_id doesn't have admin permissions
        """
        if not self._is_admin(admin_id):
            raise PermissionError("Only admins can remove collaborators")
            
        if user_id in self.collaborators:
            del self.collaborators[user_id]
            self.modified_at = datetime.utcnow()
    
    def fork(self, new_owner_id: str) -> 'Timeline':
        """
        Create a fork of this timeline
        
        Args:
            new_owner_id: ID of user who will own the fork
            
        Returns:
            Timeline: A new Timeline object with copied data and new ownership
        """
        forked = Timeline(
            id=f"{self.id}_fork_{datetime.utcnow().timestamp()}",
            title=f"Fork of {self.title}",
            description=self.description,
            dating_system=self.dating_system,
            events=[Event(**event.to_dict()) for event in self.events],
            owner_id=new_owner_id,
            parent_timeline_id=self.id
        )
        return forked
    
    def to_dict(self) -> Dict:
        """Convert timeline to dictionary for serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'dating_system': self.dating_system,
            'events': [event.to_dict() for event in self.events],
            'owner_id': self.owner_id,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
            'collaborators': {k: v.value for k, v in self.collaborators.items()},
            'parent_timeline_id': self.parent_timeline_id
        }
    
    def _can_edit(self, user_id: str) -> bool:
        """Check if user has edit permissions"""
        if user_id == self.owner_id:
            return True
        return user_id in self.collaborators and self.collaborators[user_id] in [Permission.EDIT, Permission.ADMIN]
    
    def _is_admin(self, user_id: str) -> bool:
        """Check if user has admin permissions"""
        if user_id == self.owner_id:
            return True
        return user_id in self.collaborators and self.collaborators[user_id] == Permission.ADMIN
    
    def _check_conflicts(self, event: Event, exclude_id: Optional[str] = None) -> bool:
        """
        Check if an event conflicts with existing events
        
        Args:
            event: Event to check for conflicts
            exclude_id: Optional ID of event to exclude from conflict checking
            
        Returns:
            bool: True if there are conflicts, False otherwise
        """
        # This is a placeholder for more sophisticated conflict detection
        # In a real implementation, this would need to handle the custom dating system
        # and potentially more complex conflict rules
        return False  # For now, assume no conflicts 