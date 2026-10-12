from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Type, List, Optional,Dict,Any
from pydantic import UUID4, BaseModel
from sqlalchemy.orm import validates
from sqlalchemy import asc

class  CRUDBase:
    def __init__(self, model: Type[BaseModel]):
        self.model = model

    # Create a new record
    def create(self, db: Session, obj_in: BaseModel) -> BaseModel:
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # Get a record by ID
    def get(self, db: Session, id: UUID4) -> Optional[BaseModel]:
        return db.query(self.model).filter(self.model.id == id).first()
    # Get a record by field name
    def get_by_field(self, db: Session, field: str, value: any) -> Optional[BaseModel]:
        return db.query(self.model).filter(getattr(self.model, field) == value).first()
    
    # Get all records
    def get_all(
        self, db: Session, page: int = 1, pagesize: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> List[BaseModel]:
        skip = (page - 1) * pagesize
        limit = pagesize
        query = db.query(self.model)


        # Check and apply filters dynamically
        if filters:
            for field, value in filters.items():
                if value is not None:  # Skip if the value is None
                    # Dynamically apply filter using getattr to access model attributes
                    query = db.query(self.model).filter(getattr(self.model, field) == value)
        
        return query.offset(skip).limit(limit).all()
    
    # Update a record by ID
    def update(self, db: Session, id: UUID4, obj_in: BaseModel) -> BaseModel:
        db_obj = db.query(self.model).filter(self.model.id == id).first()
        if db_obj:
            for key, value in obj_in.model_dump(exclude_unset=True, exclude_none=True).items():
                setattr(db_obj, key, value)
            db.commit()
            db.refresh(db_obj)
        return db_obj

    # Update a record by field
    def update_by_filed(self, db: Session,field: str, value: any, obj_in: BaseModel) -> BaseModel:
        db_obj = db.query(self.model).filter(getattr(self.model, field) == value).first()

        if db_obj:
            for key, value in obj_in.model_dump(exclude_unset=True, exclude_none=True).items():
                setattr(db_obj, key, value)
            db.commit()
            db.refresh(db_obj)
        return db_obj

    # Delete a record by ID
    def delete(self, db: Session, id: UUID4) -> Optional[BaseModel]:
        db_obj = db.query(self.model).filter(self.model.id == id).first()
        if db_obj:
            db.delete(db_obj)
            db.commit()
        return db_obj
    # Delete a record by FieldName
    def delete_by_field(self, db: Session,field: str, value: any) -> Optional[BaseModel]:
        db_obj = db.query(self.model).filter(getattr(self.model, field) == value).first()
        if db_obj:
            db.delete(db_obj)
            db.commit()
        return db_obj
    
    #get a count from fleds
    def get_count(self, db: Session,field: str, value: any,group_field:str) -> BaseModel:
        status_counts = (
            db.query(getattr(self.model, group_field), func.count().label("count"))
            .filter(getattr(self.model, field) == value)
            .group_by(getattr(self.model, group_field))
            .all()
        )

        # Convert the result into a dictionary
        result = {status: count for status, count in status_counts}
    
        return result