from typing import List, Optional
from pydantic import BaseModel, Field

class ContactInfo(BaseModel):
    name: str = Field(default="", description="Full name of the candidate")
    email: str = Field(default="", description="Email address of the candidate")
    phone: str = Field(default="", description="Phone number of the candidate")
    location: str = Field(default="", description="City, state, or country of residence")
    website: Optional[str] = Field(default=None, description="Personal website or portfolio link")
    linkedin: Optional[str] = Field(default=None, description="LinkedIn profile URL")
    github: Optional[str] = Field(default=None, description="GitHub profile URL")

class ExperienceItem(BaseModel):
    company: str = Field(default="", description="Company or organization name")
    role: str = Field(default="", description="Job title / role name")
    location: str = Field(default="", description="Location of company (e.g., San Francisco, CA or Remote)")
    start_date: str = Field(default="", description="Start date (e.g., June 2021)")
    end_date: str = Field(default="", description="End date (e.g., Present or August 2024)")
    description_bullets: List[str] = Field(default_factory=list, description="Bullet points detailing achievements and work")
    technologies: List[str] = Field(default_factory=list, description="Keywords / stack used in this role")

class EducationItem(BaseModel):
    institution: str = Field(default="", description="University or school name")
    degree: str = Field(default="", description="Degree level (e.g., Bachelor of Science, Master of Science)")
    field_of_study: str = Field(default="", description="Field of study / major (e.g., Computer Science)")
    location: str = Field(default="", description="Location of school")
    start_date: str = Field(default="", description="Start date of study")
    end_date: str = Field(default="", description="Graduation date or expected graduation")
    gpa: Optional[str] = Field(default=None, description="GPA scored (e.g. 3.8/4.0)")

class ProjectItem(BaseModel):
    name: str = Field(default="", description="Name of the project")
    description_bullets: List[str] = Field(default_factory=list, description="Details explaining the project scope and metrics")
    technologies: List[str] = Field(default_factory=list, description="Technologies and libraries used")
    link: Optional[str] = Field(default=None, description="Repository or live application link")

class CertificationItem(BaseModel):
    name: str = Field(default="", description="Name of certification")
    issuing_organization: str = Field(default="", description="Organization that issued the certification")
    issue_date: str = Field(default="", description="Date issued")
    expiration_date: Optional[str] = Field(default=None, description="Expiration date if any")

class ResumeSchema(BaseModel):
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    skills: List[str] = Field(default_factory=list, description="Technical and core skills")
    experiences: List[ExperienceItem] = Field(default_factory=list, description="Professional experience history")
    education: List[EducationItem] = Field(default_factory=list, description="Education details")
    projects: List[ProjectItem] = Field(default_factory=list, description="Personal and open-source projects")
    certifications: List[CertificationItem] = Field(default_factory=list, description="List of certifications")
    achievements: List[str] = Field(default_factory=list, description="Specific metrics-driven accomplishments, awards or publications")
