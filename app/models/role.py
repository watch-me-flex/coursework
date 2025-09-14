from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

class Role:
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    
    users = relationship('User', back_populates='role')

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
