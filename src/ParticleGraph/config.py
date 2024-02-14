from typing import Optional, Literal, Annotated, Dict
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ParticleGraph.config_manager import ConfigManager

from ParticleGraph import (
    GraphModel,
)


# Sub-config schemas for ParticleGraph

class SimulationConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    p: list
    radius: Annotated[float, Field(gt=0)]
    min_radius: Annotated[float, Field(ge=0)] = 0
    c: list
    n_particles: int = 1000
    n_particle_types: int = 5
    n_interactions: int = 5
    n_frames: int = 1000
    sigma: Optional[float]
    delta_t: float = 1
    v_init: float = 0
    boundary: Literal["periodic", "no"] = "periodic"
    particle_value_map: Optional[str]
    particle_type_map: Optional[str]
    beta: Optional[float]
    start_frame: int = 0


class GraphModelConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    model_type: str
    prediction: str
    input_size: int
    output_size: int
    hidden_dim: int
    n_mp_layers: int
    aggr_type: str
    embedding: int = 2
    upgrade_type: str = "none"
    n_layers_update: int = 3
    hidden_dim_update: int = 64

    def get_instance(self, **kwargs):
        return GraphModel(**self.model_dump(), **kwargs)


class PlottingConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')

    colormap: str = "tab10"
    arrow_length:  int = 10


class TrainingConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    n_epochs: int = 500
    batch_size: int = 1

    n_runs: int = 2
    clamp: float = 0
    pred_limit: float = 1.E+10
    sparsity: str = "none"

    noise_level: float = 0
    kmeans_input: str = "plot"
    data_augmentation: bool = True
    
    device: Annotated[str, Field(pattern=r'^(auto|cpu|cuda:\d+)$')] = "auto"


# Main config schema for ParticleGraph

class ParticleGraphConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')

    description: Optional[str] = "ParticleGraph"
    simulation: SimulationConfig
    graph_model: GraphModelConfig
    plotting: PlottingConfig
    training: TrainingConfig



if __name__ == '__main__':

    config_file = './config/config_test.yaml' # Insert path to config file
    raw_config = ConfigManager.load_config(config_file)

    config = ParticleGraphConfig(**raw_config)

    print('Successfully loaded config file. Model description:', config.description)
    