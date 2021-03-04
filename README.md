# UPDATE: This project will not be maintained anymore. This is because Wargaming is now using .geometry and will remove .primitive functionality, of which I made a new repository for.

# BigWorld Model Converter(.primitives)
This is a Blender addon designed to be able to import and export World of Warships' .primitives+.visual files, designed for mod authors.

## How to Add to Blender-Windows?
1. In order to add addons to Blender, first you need to locate your `addons_contrib` folder. Depending on how you installed Blender, it can be located in different places.
   * If you installed Blender with the [installer](https://www.blender.org/download/), like most people, then you can open the `addons_contrib` folder at `C:Program Files\Blender Foundation\Blender x.xx\x.xx\scripts\addons_contrib`
   * If you built Blender with Visual Studio, then you can open the `addons_contrib` folder at `C:\blender-git\build_windows_x64_vc16_Release\bin\Release\x.xx\scripts\addons_contrib`, provided you followed [this tutorial](https://wiki.blender.org/wiki/Building_Blender). If you didn't, I assume you are very experienced and already know where it is.

2. Now, download the repository and copy the `io_mesh_geometry` folder to the `addon_contrib` folder. 
3. Finally, start Blender and open the Preferences. 
4. Click on the Add-ons tab located on the left. 
5. Click on the Testing option at the top.
6. You should see the addon now, and need to click the checkmark to enable it.

## How to Add to Blender-MacOS/Linux?
If you use MacOS or Linux, take a look at [this documentation](https://docs.blender.org/manual/en/latest/editors/preferences/addons.html) to install an addon from the application.
