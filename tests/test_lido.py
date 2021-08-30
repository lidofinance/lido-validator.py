from unittest.mock import PropertyMock

from web3 import Web3

from lido import Lido
from lido.methods import (
    get_operators_indexes,
    get_operators_data,
    get_operators_keys,
    validate_keys,
    find_duplicated_keys,
)
from tests.fixtures import OPERATORS_DATA, OPERATORS_KEYS
from tests.utils import get_mainnet_provider, MockTestCase


class OperatorTest(MockTestCase):
    def setUp(self) -> None:
        self.mocker.patch('web3.eth.Eth.chain_id', return_value=1, new_callable=PropertyMock)
        self.w3 = Web3()

        self.lido = Lido(self.w3)

    def test_main_flow_methods(self):
        w3 = get_mainnet_provider()
        operators_count = get_operators_indexes(w3)[:1]

        operators_data = get_operators_data(w3, operators_count)
        operators_data[0]["totalSigningKeys"] = 30
        keys = get_operators_keys(w3, operators_data)

        invalid_keys = validate_keys(w3, keys)
        duplicates = find_duplicated_keys(keys)

        self.assertListEqual(invalid_keys, [])
        self.assertListEqual(duplicates, [])

    def test_get_operators_indexes(self):
        self.mocker.patch('lido.contract.load_contract.NodeOpsContract.getNodeOperatorsCount', return_value={"": 5})

        operator_indexes = self.lido.get_operators_indexes()
        self.assertListEqual([x for x in range(5)], operator_indexes)

    def test_get_operators_data(self):
        """We are checking that indexes are assigned correctly"""
        self.mocker.patch(
            'lido.contract.load_contract.NodeOpsContract.getNodeOperator_multicall',
            return_value=OPERATORS_DATA,
        )

        operators_data = self.lido.get_operators_data([0, 1])

        self.assertEquals(0, operators_data[0]["index"])
        self.assertEquals(1, operators_data[1]["index"])

    def test_get_operators_keys(self):
        self.mocker.patch(
            'lido.contract.load_contract.NodeOpsContract.getSigningKey_multicall',
            return_value=OPERATORS_KEYS,
        )

        operators = OPERATORS_DATA[:]

        operators[0]['index'] = 0
        operators[1]['index'] = 1

        keys = self.lido.get_operators_keys(OPERATORS_DATA)

        expected_indexes = [
            {'index': 0, 'operator_index': 0},
            {'index': 1, 'operator_index': 0},
            {'index': 0, 'operator_index': 1},
            {'index': 1, 'operator_index': 1},
            {'index': 2, 'operator_index': 1},
        ]

        for expected_key, key in zip(expected_indexes, keys):
            self.assertEquals(expected_key['index'], key['index'])
            self.assertEquals(expected_key['operator_index'], key['operator_index'])

    def test_validate_keys(self):
        self.mocker.patch(
            'lido.contract.load_contract.LidoContract.getWithdrawalCredentials',
            return_value={'': b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xb9\xd7\x93Hx\xb5\xfb\x96\x10\xb3\xfe\x8a^D\x1e\x8f\xad~)?'},
        )

        invalid_keys = self.lido.validate_keys(OPERATORS_KEYS)
        self.assertEquals(1, len(invalid_keys))

        invalid_keys = self.lido.validate_keys(OPERATORS_KEYS, strict=True)
        self.assertEquals(4, len(invalid_keys))

    def test_find_duplicated_keys(self):
        duplicates = self.lido.find_duplicated_keys([*OPERATORS_KEYS, OPERATORS_KEYS[0]])

        self.assertEquals(1, len(duplicates))
        self.assertEquals(duplicates[0][0]['key'], duplicates[0][1]['key'])