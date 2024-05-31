# models.py
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, JSON,Table
from sqlalchemy.orm import relationship,backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()



class CR(Base):
    __tablename__ = 'cr_table'

    cr_id = Column(String(45), primary_key=True)
    cr_number = Column(Integer)
    tdoc_number = Column(String(45))
    cr_title = Column(String(225))
    cr_UICC = Column(String(45))
    source_to_WG = Column(String(45))
    source_to_TSG = Column(String(45))
    work_item_code = Column(String(45))
    category = Column(String(45))
    reason_for_change = Column(Text)
    summary_of_change = Column(Text)
    consequences_if_not_approved = Column(Text)
    clauses_affected = Column(JSON)
    other_spec_affected = Column(JSON)
    other_cr_affected = Column(JSON)
    other_comments = Column(String(500))
    cr_content = Column(Text)
    spec_number = Column(String(45))
    version_number = Column(String(45))
    meeting_number = Column(String(45))
    meeting_locaton = Column(String(45))
    meeting_date = Column(Date)



class Section(Base):
    __tablename__ = 'section_table'

    section_id = Column(String(45), primary_key=True)
    section_number = Column(String(45))
    section_title = Column(String(45))
    section_content = Column(Text)
    version_id = Column(String(45), ForeignKey('spec_version_table.version_id'))
    version = relationship("SpecVersion", back_populates="sections")
    
class Specification(Base):
    __tablename__ = 'spec_table'

    spec_id = Column(String(45), primary_key=True)
    spec_number = Column(String(45))
    spec_title = Column(String(500))
    versions = relationship("SpecVersion", back_populates="spec")

class SpecVersion(Base):
    __tablename__ = 'spec_version_table'

    version_id = Column(String(45), primary_key=True)
    version_number = Column(String(45))
    release_date = Column(Date)
    spec_id = Column(String(45), ForeignKey('spec_table.spec_id'))
    spec = relationship("Specification", back_populates="versions")
    sections = relationship("Section", back_populates="version")


