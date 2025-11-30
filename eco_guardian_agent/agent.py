from google.genai import types
from google.adk.agents import Agent, LlmAgent, ParallelAgent, SequentialAgent
from google.adk.models import Gemini
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from prompts import *
from tools.air_quality import get_air_quality
from tools.disease_outbreak import (
    search_disease_outbreaks_web, 
    get_disease_outbreaks, 
    check_symptoms, 
    find_nearest_hospitals
)
from tools.uv_index import get_uv_index
from tools.weather import get_weather
from tools.pollen import get_pollen

retry_config=types.HttpRetryOptions(
    attempts=5,  
    exp_base=7, 
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504] 
)

air_quality_agent = LlmAgent(
    name="air_quality_agent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    description="Expert that retrieves the air quality and explains real-time air quality for any city.",
    instruction=AIR_QUALITY_AGENT_INSTRUCTION,
    tools=[get_air_quality],
)

weather_agent = LlmAgent(
    name="weather_agent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    description="Expert that retrieves the weather and explains real-time weather conditions for any city.",
    instruction=WEATHER_AGENT_INSTRUCTION,
    tools=[get_weather],
)

pollen_agent = LlmAgent(
    name="pollen_agent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    description="Expert that retrieves the pollen levels and explains real-time pollen conditions for any city.",
    instruction=POLLEN_AGENT_INSTRUCTION,
    tools=[get_pollen],
)

uv_agent = LlmAgent(
    name="uv_agent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    description="Expert that retrieves the UV index and explains real-time UV index for any city.",
    instruction=UV_AGENT_INSTRUCTION,
    tools=[get_uv_index],
)

events_agent = LlmAgent(
    name="events_agent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    description=(
        "Finds local events (especially environmental or outdoor events) "
        "using Google Search and summarizes them for the user."
    ),
    instruction=EVENTS_AGENT_INSTRUCTION,
    tools=[google_search],
)

outbreak_monitor = LlmAgent(
    name="outbreak_monitor",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    description="Monitors disease outbreaks globally using WHO, CDC, and public health data sources.",
    instruction=OUTBREAK_MONITOR_INSTRUCTION,
    tools=[search_disease_outbreaks_web, get_disease_outbreaks],
    output_key="outbreak_result",
)

symptom_analyzer = LlmAgent(
    name="symptom_analyzer",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    description="Analyzes symptoms and matches with disease patterns, considering local outbreak context.",
    instruction=SYMPTOM_ANALYZER_INSTRUCTION,
    tools=[check_symptoms, search_disease_outbreaks_web],
    output_key="symptom_result"
)

hospital_locator = LlmAgent(
    name="hospital_locator",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    description="Locates nearest hospitals and healthcare facilities based on user location and needs.",
    instruction=HOSPITAL_LOCATOR_INSTRUCTION,
    tools=[find_nearest_hospitals],
    output_key="hospital_result"
)

disease_coordinator = LlmAgent(
    name="disease_coordinator",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    description="Coordinates disease outbreak response by utilizing outbreak monitoring, symptom analysis, and hospital location services.",
    instruction=COORDINATOR_INSTRUCTION,
    tools=[
        search_disease_outbreaks_web,
        check_symptoms,
        find_nearest_hospitals
    ],
)

parallel_health_analysis = ParallelAgent(
    name="ParallelHealthAnalysis",
    description="Runs symptom analysis and outbreak monitoring in parallel.",
    sub_agents=[symptom_analyzer, outbreak_monitor]
)

disease_outbreak_agent = SequentialAgent(
    name="DiseaseOutbreakAgent",
    description="based on the symptoms and disease outbreak data, runs hospital locator and provides final recommendations.",
    sub_agents=[parallel_health_analysis, hospital_locator, disease_coordinator]
)

air_tool = AgentTool(agent=air_quality_agent)
weather_tool = AgentTool(agent=weather_agent)
pollen_tool = AgentTool(agent=pollen_agent)
uv_tool = AgentTool(agent=uv_agent)
events_tool = AgentTool(agent=events_agent)
disease_outbreak_tool = AgentTool(agent=disease_outbreak_agent)

root_agent = LlmAgent(
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    name='root_agent',
    description="Root coordinator agent that routes queries to specialized environmental and health agents",
    tools=[air_tool, weather_tool, pollen_tool, uv_tool, events_tool, disease_outbreak_tool],
)