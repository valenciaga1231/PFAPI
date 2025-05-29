import powerfactory as pf

def import_pfd_file(app: pf.Application):
    # Get current user folder
    current_user_folder = app.GetCurrentUser()
    if not current_user_folder:
        raise ValueError("Current user folder not found. Please ensure you are logged in to PowerFactory.")
    
    # Create new folder in the current user folder
    new_folder = current_user_folder.CreateObject("IntFolder", "y_bus_example")

    # Define the path to the PFD file and project string
    file_39_bus = 'grid_models\\39 Bus New England System.pfd'
    prj_str_39_bus = '39 Bus New England System'

    # Get and set the ComImp command
    ComImp = app.GetFromStudyCase("ComPfdImport")
    ComImp.SetAttribute("g_file", file_39_bus)
    ComImp.SetAttribute("g_target", new_folder)
    
    project_folder_name = new_folder.GetAttribute("loc_name")
    project_path = project_folder_name + "\\" + prj_str_39_bus
    ComImp.Execute() # type: ignore

    # Activate the project
    app.ActivateProject(project_path)
    project = app.GetActiveProject()
    project.Activate() # type: ignore

    return project