import powerfactory as PF
from powerfactory import DataObject
from typing import Optional

class PowerFactoryApp:
    """
    PowerFactory application
    - wrapper around the original PowerFactory application
    - singleton pattern to ensure only one instance of PowerFactoryApp is created
    - you can still call the original PowerFactory application functions using PowerFactoryApp.app
    """
    _instance: Optional['PowerFactoryApp'] = None
    
    # Singleton pattern (make sure only one instance of PowerFactoryApp is created)
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize PowerFactory application"""
        if not hasattr(self, 'app'):
            self.app = PF.GetApplicationExt()
            if self.app is None:
                # TODO: Add error codes from PF application
                raise RuntimeError("PowerFactory application could not be started.")
            print("PowerFactory application started successfully!")

    def activate_project(self, project_name: str) -> None:
        """Activate PowerFactory project"""
        if not self.app:
            raise RuntimeError("PowerFactory not initialized when activating project.")
        
        project_success = self.app.ActivateProject(project_name) # returns 0 on sucess and 1 if project cannot be found or activated
        if project_success == 1:
            raise Exception(f"Project {project_name} could not be activated.")
        print(f'Project {project_name} successfully activated')

    def activate_study_case(self, study_case_name: str) -> None:
        """Activate PowerFactory study case"""
        if not self.app:
            raise RuntimeError("PowerFactory not initialized when activating study case.")

    def get_calc_relevant_objects(self, object_type: str) -> list[DataObject]:
        """Get calculation relevant objects of specified type"""
        if not self.app:
            raise RuntimeError("PowerFactory not initialized")
        # return self.app.GetCalcRelevantObjects(object_type)
        return self.app.GetCalcRelevantObjects(object_type, 0, 0, 0) # Currently default search

    def show_gui(self) -> None:
        """Show PowerFactory GUI (NON-INTERACTIVE MODE)"""
        if self.app:
            self.app.Show()