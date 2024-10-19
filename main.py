import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import os

# Database setup
Base = declarative_base()

try:
    engine = create_engine('sqlite:///employees.db', echo=True)
    Session = sessionmaker(bind=engine)
    print("Database setup successful.")
except SQLAlchemyError as e:
    print(f"Error setting up database: {str(e)}")

class Employee(Base):
    __tablename__ = 'employees'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    position = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    salary = Column(Float, nullable=False)
    department = Column(String(100), nullable=False)

Base.metadata.create_all(engine)

# Load preexisting data from CSV
def load_csv_to_db():
    csv_path = 'employees.csv'
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            required_columns = ['name', 'position', 'email', 'salary', 'department']
            if all(col in df.columns for col in required_columns):
                # Drop the table if it exists
                Employee.__table__.drop(engine, checkfirst=True)
                # Create the table
                Base.metadata.create_all(engine)
                # Insert data
                df.to_sql('employees', engine, if_exists='append', index=False)
                print(f"Data from {csv_path} has been successfully loaded into the database.")
            else:
                print(f"Error: {csv_path} is missing one or more required columns.")
        except Exception as e:
            print(f"Error loading CSV: {str(e)}")
    else:
        print(f"CSV file not found: {csv_path}")

# Streamlit app
st.set_page_config(page_title="Employee Management System", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .main {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    h1, h2 {
        color: #1f618d;
    }
    .stButton>button {
        background-color: #2980b9;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.title("Employee Management System")

# Load CSV data
if 'db_loaded' not in st.session_state:
    st.session_state.db_loaded = False

if not st.session_state.db_loaded:
    with st.spinner("Loading data from CSV..."):
        load_csv_to_db()
        st.session_state.db_loaded = True
    st.success("Data loaded successfully!")

# CRUD operations
def load_employees():
    session = Session()
    employees = session.query(Employee).all()
    session.close()
    return employees

def add_employee(name, position, email, salary, department):
    session = Session()
    new_employee = Employee(name=name, position=position, email=email, salary=salary, department=department)
    session.add(new_employee)
    session.commit()
    session.close()

def update_employee(id, name, position, email, salary, department):
    session = Session()
    employee = session.query(Employee).get(id)
    if employee:
        employee.name = name
        employee.position = position
        employee.email = email
        employee.salary = salary
        employee.department = department
        session.commit()
    session.close()

def delete_employee(id):
    session = Session()
    employee = session.query(Employee).get(id)
    if employee:
        session.delete(employee)
        session.commit()
    session.close()

# Streamlit UI
tab1, tab2, tab3 = st.tabs(["Dashboard", "Manage Employees", "Add Employee"])

with tab1:
    st.header("Employee Dashboard")
    employees = load_employees()
    df = pd.DataFrame([(e.id, e.name, e.position, e.email, e.salary, e.department) for e in employees], 
                      columns=['ID', 'Name', 'Position', 'Email', 'Salary', 'Department'])
    
    # Key Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Employees", len(df))
    col2.metric("Average Salary", f"${df['Salary'].mean():.2f}")
    col3.metric("Number of Departments", df['Department'].nunique())
    
    # Salary Distribution
    st.subheader("Salary Distribution")
    fig = px.histogram(df, x="Salary", nbins=20)
    st.plotly_chart(fig)
    
    # Employees by Department
    st.subheader("Employees by Department")
    dept_counts = df['Department'].value_counts()
    fig = px.pie(values=dept_counts.values, names=dept_counts.index)
    st.plotly_chart(fig)

with tab2:
    st.header("Manage Employees")
    st.dataframe(df)
    
    # Edit and Delete functionality
    st.subheader("Edit or Delete Employee")
    employee_id = st.number_input("Enter Employee ID", min_value=1, step=1, key="edit_id")
    action = st.radio("Choose action", ["Edit", "Delete"], key="action")
    
    if action == "Edit":
        employee = df[df['ID'] == employee_id].iloc[0] if not df[df['ID'] == employee_id].empty else None
        if employee is not None:
            name = st.text_input("Name", value=employee['Name'], key="edit_name")
            position = st.text_input("Position", value=employee['Position'], key="edit_position")
            email = st.text_input("Email", value=employee['Email'], key="edit_email")
            salary = st.number_input("Salary", value=float(employee['Salary']), key="edit_salary")
            department = st.text_input("Department", value=employee['Department'], key="edit_department")
            if st.button("Update Employee", key="update_button"):
                update_employee(employee_id, name, position, email, salary, department)
                st.success("Employee updated successfully!")
                st.experimental_rerun()
        else:
            st.warning("Employee not found.")
    else:
        if st.button("Delete Employee", key="delete_button"):
            delete_employee(employee_id)
            st.success("Employee deleted successfully!")
            st.experimental_rerun()

with tab3:
    st.header("Add New Employee")
    name = st.text_input("Name", key="add_name")
    position = st.text_input("Position", key="add_position")
    email = st.text_input("Email", key="add_email")
    salary = st.number_input("Salary", min_value=0.0, step=1000.0, key="add_salary")
    department = st.text_input("Department", key="add_department")
    if st.button("Add Employee", key="add_button"):
        add_employee(name, position, email, salary, department)
        st.success("Employee added successfully!")
        st.experimental_rerun()
