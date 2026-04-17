"""
Climate risk pipeline — drought, heat stress, coastal-flood and composite hazard
layers for the Abidjan-Lagos corridor. Complements the existing flood layer in
gee_pipeline (JRC Global Flood DB).

Sources (all free tier):
  - SPEI drought: GEE 'CSIC/SPEI/2_9' (Standardized Precip-Evap Index)
  - Heat stress: GEE 'ECMWF/ERA5_LAND/MONTHLY' 2m_temperature extremes
  - Coastal flood: WRI Aqueduct Coastal Flood Hazard (REST) or
                   GEE 'DELTARES/floods/v2024' (inundation depth, SLR scenarios)
  - Composite risk: ThinkHazard! (GFDRR) REST — multi-hazard ranking

Usage via the pipeline bridge — agent tools should call:
    from src.adapters.pipeline_bridge import pb
    pb.get_drought_data(...)
    pb.get_heat_risk_data(...)
    pb.get_coastal_flood_data(...)
    pb.get_composite_climate_risk(...)
"""

from __future__ import annotations
