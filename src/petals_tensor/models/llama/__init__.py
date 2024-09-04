from petals_tensor.models.llama.block import WrappedLlamaBlock, WrappedLlamaBlockValidator
from petals_tensor.models.llama.config import DistributedLlamaConfig
from petals_tensor.models.llama.model import (
    DistributedLlamaForCausalLM,
    DistributedLlamaForCausalLMValidator,
    DistributedLlamaForSequenceClassification,
    DistributedLlamaModel,
)
from petals_tensor.utils.auto_config import register_model_classes

register_model_classes(
    config=DistributedLlamaConfig,
    model=DistributedLlamaModel,
    model_for_causal_lm=DistributedLlamaForCausalLM,
    model_for_causal_lm_validator=DistributedLlamaForCausalLMValidator,
    model_for_sequence_classification=DistributedLlamaForSequenceClassification,
)
