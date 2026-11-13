require("Utilities.lua")
require("Button.lua")
require("UI_ArrowWidget.lua")
require("UI_PopupWindow.lua")
require("Menu_VideoPlayer.lua")
local kSecondsBetweenTransitions = 9
local kPopupHeaderFontTag = Menu_Text("feed_popupHeaderTag")
local kPopupBodyFontTag = "\\n" .. Menu_Text("feed_popupBodyTag")
local kTransitionChore = IsPlatformSmallScreen() and "ui_feedBig_imageTransistion.chore" or "ui_feed_imageTransistion.chore"
local kFadeTime = ChoreGetLength(kTransitionChore) / 2
local mFeedWidget, mFeedThread
local mFeedData = {}
local mNumItems = 0
local mCurrentShowIndex = 0
local mNextTransitionTime = 0
local mbTransitioning = false
local mbOffline = false
local PlatformCanOpenLink = function()
  return IsPlatformPC() or IsPlatformMac() or IsPlatformIOS() or IsPlatformAndroid()
end
local getDataTable = function(feedItemData)
  local dataTable = {}
  for dataValue in string.gmatch(feedItemData, "([^,]+)") do
    table.insert(dataTable, dataValue)
  end
  return dataTable
end
local feedSetup = function()
  local feedProp = Load("feed.prop")
  if feedProp == nil then
    mbOffline = true
    CreateEventLogEvent("Dev Feed Shown", "false", true)
    return
  end
  mbOffline = false
  local lang = LangGetCurLanguage()
  if lang == "english" then
    lang = lang:gsub("%a", string.upper, 1)
  end
  local feedItems = feedProp.items
  if feedItems then
    mNumItems = table.getn(PropertyGetKeys(feedItems))
  end
  local IDsOffline = false
  for i = 0, mNumItems - 1 do
    local feedItem = feedItems and feedItems[i] or nil
    if not mFeedData[i] or table.getn(mFeedData[i]) == 0 then
      mFeedData[i] = {}
    end
    if feedItem then
      if feedItem.type then
        mFeedData[i].type = feedItem.type
      end
      if feedItem.header and feedItem.header[lang] then
        mFeedData[i].header = feedItem.header[lang]
      end
      if feedItem.Text and feedItem.Text[lang] then
        mFeedData[i].text = feedItem.Text[lang]
      end
      if feedItem.ICON then
        mFeedData[i].icon = feedItem.ICON
      end
      if feedItem.Link then
        mFeedData[i].data = feedItem.Link
      end
      if feedItem.ID then
        mFeedData[i].id = feedItem.ID
      end
      if feedItem.ID == "offline" then
        IDsOffline = true
      end
      if feedItem.max_views and tonumber(feedItem.max_views) and 1 <= tonumber(feedItem.max_views) then
        mFeedData[i].max_views = tonumber(feedItem.max_views)
      else
        mFeedData[i].max_views = "infinite"
      end
      mFeedData[i].show = true
    end
  end
  if IDsOffline then
    CreateEventLogEvent("Dev Feed Shown", "false", true)
  else
    CreateEventLogEvent("Dev Feed Shown", "true", true)
  end
end
local getPopupImageFromFeedImage = function(feedImage)
  local popupImage = "ui_imageDefault.d3dtx"
  if string.sub(feedImage, -10, -7) == "Feed" then
    local foregroundImage = string.sub(feedImage, 1, -11)
    if ResourceExists(foregroundImage .. ".d3dtx") then
      popupImage = foregroundImage .. ".d3dtx"
    end
  end
  return popupImage
end
local feedItemIsValid = function(feedData)
  if not feedData then
    return true
  end
  local feedItemId = feedData.id
  local feedItemType = feedData.type
  local feedItemData = feedData.data
  if not feedItemId then
    return false
  end
  if not feedItemType then
    return false
  end
  if not feedItemData then
    return false
  end
  if string.lower(feedItemType) == "account_link" or string.lower(feedItemType) == "accountlink" then
    return not IsTTUser() and MenuUtils_PlatformIsAccountLinkingEnabled()
  end
  if string.lower(feedItemType) == "video" then
    if not Menu_VideoPlayer_CanSupportVideo() then
      return false
    end
    local dataTable = getDataTable(feedItemData)
    if table.getn(dataTable) < 2 then
      print("UI_Feed.lua Warning: feed entry: " .. feedItemId .. " is a malformed video entry. Please fix!")
      return false
    else
      local videoPropName = dataTable[1]
      local videoPropData = PropertyGet(GetPreferences(), "DLV")[videoPropName]
      if videoPropData ~= nil then
        return Menu_VideoPlayer_GetVideoSource(videoPropName) ~= ""
      else
        print("UI_Feed.lua Warning: feed entry: " .. feedItemId .. " is a missing video name: " .. videoPropName .. ". Please fix!")
        return false
      end
    end
  end
  return true
end
local feedPopulate = function(feedData)
  local button = Clone_Find(mFeedWidget.agent, "_button")
  local message = Clone_Find(mFeedWidget.agent, "_body")
  local image = Clone_Find(mFeedWidget.agent, "_background")
  local headerText = ""
  if not feedData then
    AgentSetProperty(button, "Game Selectable", true)
    headerText = Menu_Text("feed_offline")
    AgentSetProperty(button, "Button - Command", "CreateEventLogEvent('Dev Feed Clicked', 'offline', true) Feed_OfflineClicked()")
  else
    headerText = feedData.header or ""
    local feedItemId = feedData.id or ""
    local feedItemText = feedData.text or ""
    local feedItemImage = feedData.icon or ""
    local feedItemData = feedData.data or {}
    local feedItemType = feedData.type or ""
    local eventLogCall = "CreateEventLogEvent('Dev Feed Clicked', '" .. feedItemId .. "', true) "
    if feedItemType and string.lower(feedItemType) == "lua" then
      local luaToCall = string.gsub(feedItemData, "{FEED_TEXT}", "'" .. feedItemText .. "'")
      AgentSetProperty(button, "Button - Command", eventLogCall .. luaToCall)
    elseif feedItemType and (string.lower(feedItemType) == "account_link" or string.lower(feedItemType) == "accountlink") then
      local popupText = kPopupHeaderFontTag .. headerText .. kPopupBodyFontTag .. feedItemText
      local popupImage = getPopupImageFromFeedImage(feedItemImage)
      AgentSetProperty(button, "Button - Command", eventLogCall .. "if (not IsTTUser() and MenuUtils_PlatformIsAccountLinkingEnabled()) then MenuUtils_ChallengeAccountLink('" .. popupText .. "', '" .. popupImage .. "', 'Feed') end")
    elseif feedItemType and string.lower(feedItemType) == "video" then
      local dataTable = getDataTable(feedItemData)
      local videoPropName = dataTable[1]
      local episodeContent = tonumber(dataTable[2])
      AgentSetProperty(button, "Button - Command", eventLogCall .. "Menu_VideoMenu_PlayVideo('" .. tostring(videoPropName) .. "', " .. episodeContent .. ", false)")
    elseif feedItemType and string.lower(feedItemType) == "forum" then
      local popupText = kPopupHeaderFontTag .. headerText .. kPopupBodyFontTag .. feedItemText
      AgentSetProperty(button, "Game Selectable", true)
      AgentSetProperty(button, "Button - Command", eventLogCall .. "Feed_ForumClicked(\"" .. feedItemData .. "\", \"" .. feedItemId .. "\", \"" .. popupText .. "\", \"" .. feedItemImage .. "\")")
    else
      local popupText = kPopupHeaderFontTag .. headerText .. kPopupBodyFontTag .. feedItemText
      AgentSetProperty(button, "Game Selectable", true)
      AgentSetProperty(button, "Button - Command", eventLogCall .. "Feed_Clicked(\"" .. feedItemData .. "\", \"" .. feedItemId .. "\", \"" .. popupText .. "\", \"" .. feedItemImage .. "\")")
    end
    local feedImage = "ui_imageDefaultFeed.d3dtx"
    if ResourceExists(feedItemImage) then
      feedImage = feedItemImage
    end
    ShaderOverrideTexture(image, "ui_feed_imageHolder.d3dtx", feedImage)
  end
  AgentSetProperty(message, "Text String", headerText)
end
local feedUpdate = function(feedWidget)
  mNextTransitionTime = GetTotalTime() + kSecondsBetweenTransitions
  while true do
    if GetTotalTime() < mNextTransitionTime then
      if feedWidget.paused then
        mNextTransitionTime = GetTotalTime() + kSecondsBetweenTransitions
      end
      WaitForNextFrame()
    else
      Feed_CycleRight(false)
      WaitForNextFrame()
    end
  end
end
local getNextValidFeedIndex = function(index, bRight)
  local runningIndex = index
  if bRight then
    while runningIndex <= mNumItems - 1 do
      if feedItemIsValid(mFeedData[runningIndex]) then
        return runningIndex
      end
      runningIndex = runningIndex + 1
    end
    runningIndex = 0
    while index > runningIndex do
      if feedItemIsValid(mFeedData[runningIndex]) then
        return runningIndex
      end
      runningIndex = runningIndex + 1
    end
  else
    while 0 <= runningIndex do
      if feedItemIsValid(mFeedData[runningIndex]) then
        return runningIndex
      end
      runningIndex = runningIndex - 1
    end
    runningIndex = mNumItems - 1
    while index < runningIndex do
      if feedItemIsValid(mFeedData[runningIndex]) then
        return runningIndex
      end
      runningIndex = runningIndex - 1
    end
  end
  return nil
end

function Feed_CycleLeft(bLogEvent)
  if mbTransitioning then
    return
  end
  mbTransitioning = true
  mCurrentShowIndex = getNextValidFeedIndex(mCurrentShowIndex - 1, false)
  mNextTransitionTime = GetTotalTime() + kSecondsBetweenTransitions
  local controller = ChorePlayToTime(kTransitionChore, kFadeTime, nil, true, unpack(Clone_GetChoreRemapping(kTransitionChore, mFeedWidget.agent)))
  feedPopulate(mFeedData[mCurrentShowIndex])
  ControllerPlay(controller)
  ControllerWait(controller)
  if bLogEvent ~= false then
    CreateEventLogEvent("UI Feed Cycle Left", mFeedData[mCurrentShowIndex].id, true)
  end
  mbTransitioning = false
end

function Feed_CycleRight(bLogEvent)
  if mbTransitioning then
    return
  end
  mbTransitioning = true
  mCurrentShowIndex = getNextValidFeedIndex(mCurrentShowIndex + 1, true)
  mNextTransitionTime = GetTotalTime() + kSecondsBetweenTransitions
  local controller = ChorePlayToTime(kTransitionChore, kFadeTime, nil, true, unpack(Clone_GetChoreRemapping(kTransitionChore, mFeedWidget.agent)))
  feedPopulate(mFeedData[mCurrentShowIndex])
  ControllerPlay(controller)
  ControllerWait(controller)
  if bLogEvent ~= false then
    CreateEventLogEvent("UI Feed Cycle Right", mFeedData[mCurrentShowIndex].id, true)
  end
  mbTransitioning = false
end

function Feed_OfflineClicked()
  local popupImage = "ui_imageDefault.d3dtx"
  local popupArgs = {
    message = "popupSplash_offlineFeed",
    texture = popupImage,
    buttons = {
      {text = "label_ok", command = "Menu_Pop()"}
    }
  }
  Menu_PopupWindow(popupArgs)
end

function Feed_ForumClicked(url, feedId, popupText, feedImage)
  local popupImage = getPopupImageFromFeedImage(feedImage)
  local popupArgs
  if PlatformCanOpenLink() then
    popupArgs = {
      message = popupText,
      texture = popupImage,
      buttons = {
        {
          text = "label_goToForum",
          command = "Feed_GoToUrl( '" .. url .. "', '" .. feedId .. "' ) Menu_Pop()",
          eventLog = "Feed Popup: Go To Forum"
        },
        {
          text = "label_notNow",
          command = "Menu_Pop()",
          eventLog = "Feed Popup: Cancel Forum"
        }
      }
    }
  else
    popupArgs = {
      message = popupText,
      texture = popupImage,
      buttons = {
        {
          text = "label_gotIt",
          command = "Menu_Pop()"
        }
      }
    }
  end
  Menu_PopupWindow(popupArgs)
end

function Feed_Clicked(url, feedId, popupText, feedImage)
  local popupImage = getPopupImageFromFeedImage(feedImage)
  local popupArgs
  if PlatformCanOpenLink() then
    popupArgs = {
      message = popupText,
      texture = popupImage,
      buttons = {
        {
          text = "label_goToWebsite",
          command = "Feed_GoToUrl( '" .. url .. "', '" .. feedId .. "' ) Menu_Pop()",
          eventLog = "Feed Popup: Go To Web"
        },
        {
          text = "label_notNow",
          command = "Menu_Pop()",
          eventLog = "Feed Popup: Cancel Web"
        }
      }
    }
  else
    popupArgs = {
      message = popupText,
      texture = popupImage,
      buttons = {
        {
          text = "label_gotIt",
          command = "Menu_Pop()"
        }
      }
    }
  end
  Menu_PopupWindow(popupArgs)
end

function Feed_GoToUrl(url, feedId)
  local urlToUse = MenuUtils_AppendUrlData(url, "feed", feedId)
  PlatformOpenURL(urlToUse)
  CreateEventLogEvent("Platform Open URL", url, true)
end

Feed = Class(Widget)

function Feed:Initialize(name)
  Widget.Initialize(self, name)
  feedSetup()
  mFeedWidget = self
end

function Feed:OnDestroyed()
  Widget.OnDestroyed(self)
  if mFeedThread then
    ThreadKill(mFeedThread)
  end
end

function Feed:CreateAgent(name, scene)
  if IsPlatformSmallScreen() then
    return Clone(name, "ui_feed_reference", "ui_feedBig.scene", scene)
  else
    return Clone(name, "ui_feed_reference", "ui_feed.scene", scene)
  end
end

function Feed:CreateArrowAgents(menuWidget)
  local feedAgent = self.agent
  self.leftArrow = Menu_Insert(menuWidget, MenuArrow, "feed_arrowLeft", "left", "Feed_CycleLeft()")
  AgentAttach(self.leftArrow.agent, feedAgent)
  
  function self.leftArrow:Place()
    self:AnchorToAgent(feedAgent, "outside_left", "center")
  end
  
  self.rightArrow = Menu_Insert(menuWidget, MenuArrow, "feed_arrowRight", "right", "Feed_CycleRight()")
  AgentAttach(self.rightArrow.agent, feedAgent)
  
  function self.rightArrow:Place()
    self:AnchorToAgent(feedAgent, "outside_right", "center")
  end
  
  if mbOffline then
    self.rightArrow:Suppress("offlineMode", true)
  end
end

function Feed:Show()
  Widget.Show(self, true, false, false)
  if mbOffline then
    self.rightArrow:Suppress("offlineMode", true)
    self.leftArrow:Suppress("offlineMode", true)
  end
  local button = Clone_Find(self.agent, "_button")
  local body = Clone_Find(self.agent, "_body")
  local image = Clone_Find(self.agent, "_image")
  local background = Clone_Find(self.agent, "_background")
  AgentHide(button, true)
  AgentHide(body, true)
  AgentHide(image, true)
  AgentHide(background, true)
  AgentSetProperty(button, "Game Selectable", true)
  if mFeedThread then
    ThreadKill(mFeedThread)
  end
  self:OnWidgetInputChange(Input_UseCursor())
  if mbOffline then
    feedPopulate(nil)
  else
    mCurrentShowIndex = getNextValidFeedIndex(0, true)
    if mCurrentShowIndex ~= nil then
      feedPopulate(mFeedData[mCurrentShowIndex])
      mFeedThread = ThreadStart(feedUpdate, self)
    else
      mbOffline = true
      feedPopulate(nil)
      self.rightArrow:Suppress("offlineMode", true)
      self.leftArrow:Suppress("offlineMode", true)
    end
  end
  AgentHide(body, false)
  AgentHide(image, false)
  AgentHide(background, false)
  ChorePlayOnAgent("ui_feed_show.chore", self.agent, 100, true)
  AgentHide(button, false)
end

function Feed:Hide()
  ChorePlayOnAgent("ui_feed_hide.chore", self.agent)
  self.leftArrow:Hide()
  self.rightArrow:Hide()
  ThreadKill(mFeedThread)
  Widget.Hide(self)
end

function Feed:OnWidgetInputChange(bUseCursor)
  if not self.shown then
    return
  end
  local buttonLeft = Clone_Find(self.agent, "_buttonLeft")
  local buttonRight = Clone_Find(self.agent, "_buttonRight")
  AgentHide(buttonLeft, bUseCursor or mbOffline or self.paused)
  AgentHide(buttonRight, bUseCursor or mbOffline or self.paused)
  if not bUseCursor or mbOffline or self.paused then
    self.leftArrow:Suppress("input", true)
    self.rightArrow:Suppress("input", true)
  else
    self.leftArrow:Unsuppress("input", true)
    self.rightArrow:Unsuppress("input", true)
  end
end

function Feed:onModalPushed()
  self.paused = true
  self:OnWidgetInputChange(Input_UseCursor())
end

function Feed:onModalPopped()
  self.paused = false
  self:OnWidgetInputChange(Input_UseCursor())
end

function Feed:OnLeftStick(button, event)
  if mbOffline then
    return
  end
  local button = Buttons_GetSelected(AgentGetScene(self.agent))
  if button == Clone_Find(self.agent, "_button") then
    local dir = 0
    if math.abs(event.x) > 0.1 and math.abs(event.x) > math.abs(event.y) then
      WidgetInputHandler_ConsumeEvent(event)
      if 0 < event.x then
        dir = 1
      else
        dir = -1
      end
    end
    if dir ~= self.stickDir then
      self.stickDir = dir
      if dir ~= 0 then
        if dir == 1 then
          self:OnRight(button, event)
        else
          self:OnLeft(button, event)
        end
      end
    end
  end
end

function Feed:OnLeft(button, event)
  if mbOffline then
    return
  end
  local button = Buttons_GetSelected(AgentGetScene(self.agent))
  if button == Clone_Find(self.agent, "_button") then
    WidgetInputHandler_ConsumeEvent(event)
    Feed_CycleLeft()
  end
end

function Feed:OnRight(button, event)
  if mbOffline then
    return
  end
  local button = Buttons_GetSelected(AgentGetScene(self.agent))
  if button == Clone_Find(self.agent, "_button") then
    WidgetInputHandler_ConsumeEvent(event)
    Feed_CycleRight()
  end
end

function Feed:OnL(button, event)
  if mbOffline then
    return
  end
  local button = Clone_Find(self.agent, "_button")
  button:Select(true)
  Feed_CycleLeft()
end

function Feed:OnR(button, event)
  if mbOffline then
    return
  end
  local button = Clone_Find(self.agent, "_button")
  button:Select(true)
  Feed_CycleRight()
end
