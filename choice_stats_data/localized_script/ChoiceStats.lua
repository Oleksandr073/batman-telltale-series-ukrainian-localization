require("SessionProperties.lua")
require("EventLog.lua")
local kNumEpisodes = 5
local mLog, mNodes, mExpressions
local mDebug = {}
if IsDebugBuild() then
  for i = 1, kNumEpisodes do
    mDebug[i] = SessionProperties_Get("choices debug " .. i)
  end
end
local processExpressions = function(expressions)
  mNodes = {}
  local nodeSet = {}
  local query = {}
  for i, expression in pairs(expressions) do
    for id in string.gmatch(expression, "[0-9A-F-]+") do
      if not nodeSet[id] then
        nodeSet[id] = id
        table.insert(query, {
          tag = "Executing Dialog Node",
          data = "{" .. id .. "}"
        })
      end
    end
  end
  local episodeSkipped = SaveLoad_GetSlotValue("Episodes Skipped")
  local playset = SaveLoad_GetSlotValue("Generated Choices ID")
  if episodeSkipped and episodeSkipped ~= "" then
    local skippedEpisodes = {}
    for i = 1, string.len(episodeSkipped) do
      local num = tonumber(string.sub(episodeSkipped, i, i))
      if num then
        table.insert(skippedEpisodes, num)
      end
    end
    if not playset or playset == 0 then
      playset = 1
    end
    for i, v in ipairs(skippedEpisodes) do
      local theLog = "generatedLog10" .. v .. "A"
      if playset == 1 then
        theLog = "generatedLog10" .. v .. "A"
      end
      if playset == 2 then
        theLog = "generatedLog10" .. v .. "B"
      end
      if not ResourceExists(theLog .. ".estore") then
        print("ChoiceStats.lua Error: We're trying to Query a Generated Random Choice That Doesn't Have a Log for " .. theLog)
        break
      end
      local playsetLog = QueryEventLog(FileSetExtension(theLog, "estore"), query)
      if playsetLog then
        for i, v in ipairs(playsetLog) do
          local node = v.data
          mNodes[node] = true
        end
      end
    end
  end
  local result = QueryEventLog(FileSetExtension(mLog, "estore"), query)
  if result then
    for i, v in ipairs(result) do
      local node = v.data
      mNodes[node] = true
    end
  else
    print("No Event Log")
  end
end
local getLogData = function()
  if mNodes then
    return
  end
  mNodes = {}
  if not ResourceExists(FileSetExtension(mLog, "estore")) then
    return
  end
  local expressions = mExpressions
  if not expressions then
    if not ResourceExists("choice.prop") then
      return
    end
    expressions = {}
    local choices = PropertyGet("choice.prop", "Choices")
    local i = 0
    while PropertyExists(choices, i) do
      local choice = PropertyGet(choices, i)
      local options = PropertyGet(choice, "Options")
      local j = 0
      while PropertyExists(options, j) do
        local option = PropertyGet(options, j)
        table.insert(expressions, PropertyGet(option, "expression"))
        j = j + 1
      end
      i = i + 1
    end
  end
  processExpressions(expressions)
end
local seenNode = function(nodeID)
  getLogData()
  nodeID = string.gsub(nodeID, "[{}]", "")
  nodeID = "{" .. nodeID .. "}"
  for k, v in pairs(mNodes) do
    if type(nodeID) == "string" then
      nodeID = StringToSymbol(nodeID)
    end
    if k == nodeID then
      return true
    end
  end
  return false
end

function ChoiceStats_Init(log, expressionList)
  mNodes = nil
  mLog = log or mLog or EventLog_GetLogName()
  mExpressions = expressionList
end

local trim = function(str)
  return string.gsub(string.gsub(str, "^%s*", ""), "%s*$", "")
end
local subexpr = function(str)
  local n = 1
  while str:sub(n, n) == "~" do
    n = n + 1
  end
  if str:sub(n, n) == "(" then
    local parens = 1
    local len = str:len()
    while n <= len and 0 < parens do
      n = n + 1
      local char = str:sub(n, n)
      if char == "(" then
        parens = parens + 1
      elseif char == ")" then
        parens = parens - 1
      end
    end
  end
  local op = str:find("[&|]", n)
  if op then
    return trim(str:sub(1, op - 1)), str:sub(op, op), trim(str:sub(op + 1))
  else
    return str
  end
end

function ChoiceStats_Evaluate(nodeString, optEpisode)
  if optEpisode and mDebug[tonumber(string.sub(tostring(optEpisode), -1))] then
    return true
  end
  nodeString = trim(nodeString)
  local lastop = "&"
  local lastval = true
  while nodeString ~= "" do
    local first, op, second = subexpr(nodeString)
    local inverse = false
    while first:sub(1, 1) == "~" do
      inverse = not inverse
      first = first:sub(2)
    end
    local val
    if first:sub(1, 1) == "(" and first:sub(-1, -1) == ")" then
      val = ChoiceStats_Evaluate(first:sub(2, -2))
    elseif first == "t" then
      val = true
    elseif first == "f" then
      val = false
    else
      val = seenNode(first)
    end
    if inverse then
      val = not val
    end
    if lastop == "&" then
      val = lastval and val
    else
      val = lastval or val
    end
    if op == nil then
      return val
    elseif val and op == "|" then
      return true
    elseif not val and op == "&" then
      return false
    end
    lastop = op
    lastval = val
    nodeString = second
  end
  return false
end

function ChoiceStats_GetFirstOption(choice)
  local options = PropertyGet(choice, "Options")
  local i = 0
  while PropertyExists(options, i) do
    local option = PropertyGet(options, i)
    local expression = PropertyGet(option, "expression")
    if ChoiceStats_Evaluate(expression, PropertyGet(choice, "Episode")) then
      return option
    end
    i = i + 1
  end
end

function ChoiceStats_LocalizeText(props)
  if not props then
    return ""
  end
  local lang = LangGetCurLanguage()
  if lang and PropertyExists(props, lang) then
    return PropertyGet(props, lang)
  else
    return PropertyGet(props, "English")
  end
end

local mSeenEntries
local mbSeenNeedsSave = false
local getSeenEntries = function()
  if not mSeenEntries then
    mSeenEntries = {}
    local bundle = SaveLoad_GetSlot()
    if ResourceExists(bundle) then
      local data = BundleGetResource(bundle, "choicestats.prop")
      if data then
        data = PropertyGet(data, "Seen")
        if data then
          string.gsub(data, "([^'\t']+)", function(id)
            mSeenEntries[id] = id
          end)
        end
      end
    end
  end
  return mSeenEntries
end

function ChoiceStats_MakeSeen(id)
  getSeenEntries()
  if not mSeenEntries[id] then
    mSeenEntries[id] = id
    mbSeenNeedsSave = true
  end
end

function ChoiceStats_IsSeen(id)
  return getSeenEntries()[id]
end

function ChoiceStats_SaveSeen(id)
  if mbSeenNeedsSave then
    local list = {}
    for id, v in pairs(mSeenEntries) do
      table.insert(list, id)
    end
    local str = table.concat(list, "\t")
    local bundle = SaveBundle_Create(SaveLoad_GetSlot())
    local data = BundleGetResource(bundle, "choicestats.prop") or BundleCreateResource(bundle, "choicestats.prop")
    if data then
      PropertyClearKeys(data)
      PropertyCreate(data, "Seen", "string", str)
    end
    Save(bundle)
    mbSeenNeedsSave = false
  end
end

function ChoiceStats_IsNew(node)
  ChoiceStats_Init()
  if node then
    return not ChoiceStats_IsSeen(node)
  else
    local choices = PropertyGet("choice.prop", "Choices")
    local i = 0
    while PropertyExists(choices, i) do
      local choice = PropertyGet(choices, i)
      local options = PropertyGet(choice, "Options")
      local j = 0
      while PropertyExists(options, j) do
        local option = PropertyGet(options, j)
        local node = PropertyGet(option, "expression")
        if node and ChoiceStats_Evaluate(node) and ChoiceStats_IsNew(node) then
          return true
        end
        j = j + 1
      end
      i = i + 1
    end
    return false
  end
end

function ChoiceStats_IsEmpty(optEpisode)
  ChoiceStats_Init()
  if optEpisode then
    if mDebug[tonumber(string.sub(tostring(optEpisode), -1))] then
      return false
    end
  else
    for i = 1, kNumEpisodes do
      if mDebug[i] then
        return false
      end
    end
  end
  if not ResourceExists("choice.prop") then
    return true
  end
  local choices = PropertyGet("choice.prop", "Choices")
  local i = 0
  while PropertyExists(choices, i) do
    local choice = PropertyGet(choices, i)
    if optEpisode == nil or optEpisode == PropertyGet(choice, "episode") then
      local options = PropertyGet(choice, "Options")
      local j = 0
      while PropertyExists(options, j) do
        local option = PropertyGet(options, j)
        local node = PropertyGet(option, "expression")
        if ChoiceStats_Evaluate(node) then
          return false
        end
        j = j + 1
      end
    end
    i = i + 1
  end
  return true
end

function ChoiceStats_ToggleDebug(episode)
  if not IsDebugBuild() then
    return
  end
  episode = tonumber(string.sub(tostring(episode), -1))
  local key = "choices debug " .. episode
  mDebug[episode] = not mDebug[episode]
  SessionProperties_Set(key, mDebug[episode], "Bool")
end

function ChoiceStats_IsDebugActive(episode)
  if not IsDebugBuild() then
    return false
  end
  if episode then
    episode = tonumber(string.sub(tostring(episode), -1))
    return mDebug[episode]
  else
    for i = 1, kNumEpisodes do
      if mDebug[i] then
        return true
      end
    end
    return false
  end
end

if IsToolBuild() then
  local episode = SubProject_GetEpisodeNumber()
  ProjectMenu_AddProjectCommand("Toggle Debug Choices", Bind(ChoiceStats_ToggleDebug, episode), Bind(ChoiceStats_IsDebugActive, episode), "UI")
end
