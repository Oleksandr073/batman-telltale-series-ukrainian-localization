require("ClickText.lua")
require("Menu_ListMenu.lua")
require("UI_Header.lua")
require("UI_TextWidget.lua")
local kAboutTextProp = "ui_aboutText.prop"
local kAboutTextBigProp = "ui_aboutTextBig.prop"
AboutTextWidget = Class(TextWidget)
AboutTextWidget.propFile = IsPlatformSmallScreen() and kAboutTextBigProp or kAboutTextProp
local CreateAssets = function()
  local fileName = kAboutTextProp
  if CreateResource(fileName, kDirProperties, "Menu") then
    PropertyAddGlobal(fileName, "ui_textWidget.prop")
    PropertySet(fileName, "Text Width", 8)
    PropertySet(fileName, "Text Padding Top", 0.2)
    Save(fileName)
  end
  fileName = kAboutTextBigProp
  if CreateResource(fileName, kDirProperties, "Menu") then
    PropertyAddGlobal(fileName, kAboutTextProp)
    Save(fileName)
  end
end

function Menu_About()
  local menu = Menu_Create(ListMenu, "ui_menuAbout")
  menu.align = "left"
  
  function menu:Show(intDirection)
    if intDirection ~= nil and 0 < intDirection then
      local eventLogData
      if AgentExists("ui_menuPause.scene") then
        ChorePlay("ui_menuPause_transitionSettingsSubMenusIn.chore")
        eventLogData = "AV Pause"
      else
        ChorePlay("ui_keyArt_transitionSettingsSubMenusIn.chore")
        eventLogData = "AV Main Menu"
      end
      CreateEventLogEvent("Setting Menu Page Shown", eventLogData, true)
    end
    Menu.Show(self)
    ClickText_Enable(true)
  end
  
  function menu:Hide(intDirection)
    ClickText_Enable(false)
    Menu.Hide(self)
    if intDirection ~= nil and intDirection < 0 then
      if AgentExists("ui_menuPause.scene") then
        ChorePlay("ui_menuPause_transitionSettingsSubMenusOut.chore")
      else
        ChorePlay("ui_keyArt_transitionSettingsSubMenusOut.chore")
      end
    end
  end
  
  function menu:Populate()
    Menu_Add(Header, nil, "header_about")
    local aboutText = Menu_Text("about_text")
    aboutText = string.gsub(aboutText, "{BUILD_VERSION}", PlatformGetBuildVersion())
    aboutText = string.gsub(aboutText, "{ENGINE_VERSION}", EngineGetVersion())
    local textBodyWidget = Menu_Add(AboutTextWidget, "body", aboutText)
    Legend_Add("faceButtonRight", "legend_previousMenu", "Menu_Pop()")
    local legendWidget = Menu_Add(Legend)
    
    function legendWidget:Place()
      self:AnchorToAgent(menu.agent, menu.align, "bottom")
    end
    
    local legendButton = Menu_Add(LegendButtonBack, "legendButton_back", "Menu_Pop()", "legendButton_back")
    
    function legendButton:Place()
      self:AnchorToAgent(menu.agent, menu.align, "bottom")
    end
  end
  
  Menu_Push(menu)
end

if IsToolBuild() then
  CreateAssets()
end
