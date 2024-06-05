from petals_tensor.models.bloom.block import WrappedBloomBlock
from petals_tensor.models.bloom.config import DistributedBloomConfig
from petals_tensor.models.bloom.model import (
    DistributedBloomForCausalLM,
    DistributedBloomForSequenceClassification,
    DistributedBloomModel,
)
from petals_tensor.utils.auto_config import register_model_classes

register_model_classes(
    config=DistributedBloomConfig,
    model=DistributedBloomModel,
    model_for_causal_lm=DistributedBloomForCausalLM,
    model_for_sequence_classification=DistributedBloomForSequenceClassification,
)
