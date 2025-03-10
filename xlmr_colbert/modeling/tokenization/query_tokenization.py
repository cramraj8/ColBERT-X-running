import torch

from transformers import XLMRobertaTokenizer
from xlmr_colbert.modeling.tokenization.utils import _split_into_batches


class QueryTokenizer():
    def __init__(self, query_maxlen):
        self.tok = XLMRobertaTokenizer.from_pretrained('xlm-roberta-large')
        self.tok.add_tokens(['[unused1]'])
        self.tok.add_tokens(['[unused2]'])
        self.query_maxlen = query_maxlen

        self.Q_marker_token, self.Q_marker_token_id = '[Q]', 250002
        self.cls_token, self.cls_token_id = self.tok.cls_token, self.tok.cls_token_id
        self.sep_token, self.sep_token_id = self.tok.sep_token, self.tok.sep_token_id
        self.mask_token, self.mask_token_id = self.tok.mask_token, self.tok.mask_token_id

        assert self.Q_marker_token_id == 250002 and self.mask_token_id == 250001

    def tokenize(self, batch_text, add_special_tokens=False):
        assert type(batch_text) in [list, tuple], (type(batch_text))

        tokens = [self.tok.tokenize(x, add_special_tokens=False) for x in batch_text]

        if not add_special_tokens:
            return tokens

        prefix, suffix = [self.cls_token, self.Q_marker_token], [self.sep_token]
        tokens = [prefix + lst + suffix + [self.mask_token] * (self.query_maxlen - (len(lst)+3)) for lst in tokens]

        return tokens

    def encode(self, batch_text, add_special_tokens=False):
        assert type(batch_text) in [list, tuple], (type(batch_text))

        ids = self.tok(batch_text, add_special_tokens=False)['input_ids']

        if not add_special_tokens:
            return ids

        prefix, suffix = [self.cls_token_id, self.Q_marker_token_id], [self.sep_token_id]
        ids = [prefix + lst + suffix + [self.mask_token_id] * (self.query_maxlen - (len(lst)+3)) for lst in ids]

        return ids

    def tensorize(self, batch_text, bsize=None):
        assert type(batch_text) in [list, tuple], (type(batch_text))

        # add placehold for the [Q] marker
        batch_text = ['. ' + x for x in batch_text]

        obj = self.tok(batch_text, padding='max_length', truncation=True,
                       return_tensors='pt', max_length=self.query_maxlen)

        ids, mask = obj['input_ids'], obj['attention_mask']

        # postprocess for the [Q] marker and the [MASK] augmentation
        ids[:, 1] = self.Q_marker_token_id
        ids[ids == 1] = self.mask_token_id

        if bsize:
            batches = _split_into_batches(ids, mask, bsize)
            return batches

        return ids, mask

    # def tensorize(self, batch_text, bsize=None):
    #     assert type(batch_text) in [list, tuple], (type(batch_text))

    #     # add placehold for the [Q] marker
    #     batch_text = ['. ' + x for x in batch_text]

    #     obj = self.tok(batch_text, padding='max_length', truncation=True,
    #                    return_tensors='pt', max_length=self.query_maxlen)

    #     ids, mask = obj['input_ids'], obj['attention_mask']
        
    #     ### ADDED ramraj
    #     token_type_ids = obj["token_type_ids"]
    #     # fix broken token type id for XLMR
    #     if token_type_ids[0].sum()==0:
    #         token_type_ids = (ids == self.tok.eos_token_id)
    #         token_type_ids = token_type_ids.cumsum(1)
    #         token_type_ids = (token_type_ids < 2).to(token_type_ids.dtype)
    #         #token_type_ids = (token_type_ids==2) & ~(special_tokens_mask)
    #     mask = (mask == 1) & (token_type_ids == 1)

    #     # postprocess for the [Q] marker and the [MASK] augmentation
    #     ids[:, 1] = self.Q_marker_token_id
    #     ids[ids == 1] = self.mask_token_id

    #     if bsize:
    #         batches = _split_into_batches(ids, mask, bsize)
    #         return batches

    #     return ids, mask

