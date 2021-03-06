# Copyright 2015 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Tests for manipulating Baymodel via the DB API"""

import six

from magnum.common import exception
from magnum.common import utils as magnum_utils
from magnum.tests.unit.db import base
from magnum.tests.unit.db import utils


class DbBaymodelTestCase(base.DbTestCase):

    def _create_test_baymodel(self, **kwargs):
        bm = utils.get_test_baymodel(**kwargs)
        self.dbapi.create_baymodel(bm)
        return bm

    def test_get_baymodel_list(self):
        uuids = []
        for i in range(1, 6):
            bm = utils.get_test_baymodel(id=i,
                                         uuid=magnum_utils.generate_uuid())
            self.dbapi.create_baymodel(bm)
            uuids.append(six.text_type(bm['uuid']))
        res = self.dbapi.get_baymodel_list(self.context)
        res_uuids = [r.uuid for r in res]
        self.assertEqual(sorted(uuids), sorted(res_uuids))

    def test_get_baymodel_list_with_filters(self):
        bm1 = self._create_test_baymodel(
            id=1,
            name='bm-one',
            uuid=magnum_utils.generate_uuid(),
            image_id='image1')
        bm2 = self._create_test_baymodel(
            id=2,
            name='bm-two',
            uuid=magnum_utils.generate_uuid(),
            image_id='image2')

        res = self.dbapi.get_baymodel_list(self.context,
                                           filters={'name': 'bm-one'})
        self.assertEqual([bm1['id']], [r.id for r in res])

        res = self.dbapi.get_baymodel_list(self.context,
                                           filters={'name': 'bad-name'})
        self.assertEqual([], [r.id for r in res])

        res = self.dbapi.get_baymodel_list(self.context,
                                           filters={'image_id': 'image1'})
        self.assertEqual([bm1['id']], [r.id for r in res])

        res = self.dbapi.get_baymodel_list(self.context,
                                           filters={'image_id': 'image2'})
        self.assertEqual([bm2['id']], [r.id for r in res])

    def test_get_baymodel_by_id(self):
        bm = self._create_test_baymodel()
        baymodel = self.dbapi.get_baymodel_by_id(self.context, bm['id'])
        self.assertEqual(bm['uuid'], baymodel.uuid)

    def test_get_baymodel_by_uuid(self):
        bm = self._create_test_baymodel()
        baymodel = self.dbapi.get_baymodel_by_uuid(self.context, bm['uuid'])
        self.assertEqual(bm['id'], baymodel.id)

    def test_get_baymodel_that_does_not_exist(self):
        self.assertRaises(exception.BayModelNotFound,
                          self.dbapi.get_baymodel_by_id, self.context, 666)

    def test_get_baymodel_by_name(self):
        bm = self._create_test_baymodel()
        res = self.dbapi.get_baymodel_by_name(self.context, bm['name'])
        self.assertEqual(bm['id'], res.id)
        self.assertEqual(bm['uuid'], res.uuid)

    def test_get_baymodel_by_name_multiple_baymodel(self):
        self._create_test_baymodel(
            id=1, name='bm',
            uuid=magnum_utils.generate_uuid(),
            image_id='image1')
        self._create_test_baymodel(
            id=2, name='bm',
            uuid=magnum_utils.generate_uuid(),
            image_id='image2')
        self.assertRaises(exception.Conflict, self.dbapi.get_baymodel_by_name,
                          self.context, 'bm')

    def test_get_baymodel_by_name_not_found(self):
        self.assertRaises(exception.BayModelNotFound,
                          self.dbapi.get_baymodel_by_name,
                          self.context, 'not_found')

    def test_update_baymodel(self):
        bm = self._create_test_baymodel()
        res = self.dbapi.update_baymodel(bm['id'], {'name': 'updated-model'})
        self.assertEqual('updated-model', res.name)

    def test_update_baymodel_that_does_not_exist(self):
        self.assertRaises(exception.BayModelNotFound,
                          self.dbapi.update_baymodel, 666, {'name': ''})

    def test_update_baymodel_uuid(self):
        bm = self._create_test_baymodel()
        self.assertRaises(exception.InvalidParameterValue,
                          self.dbapi.update_baymodel, bm['id'],
                          {'uuid': 'hello'})

    def test_destroy_baymodel(self):
        bm = self._create_test_baymodel()
        self.dbapi.destroy_baymodel(bm['id'])
        self.assertRaises(exception.BayModelNotFound,
                          self.dbapi.get_baymodel_by_id,
                          self.context, bm['id'])

    def test_destroy_baymodel_by_uuid(self):
        uuid = magnum_utils.generate_uuid()
        self._create_test_baymodel(uuid=uuid)
        self.assertIsNotNone(self.dbapi.get_baymodel_by_uuid(self.context,
                                                             uuid))
        self.dbapi.destroy_baymodel(uuid)
        self.assertRaises(exception.BayModelNotFound,
                          self.dbapi.get_baymodel_by_uuid, self.context, uuid)

    def test_destroy_baymodel_that_does_not_exist(self):
        self.assertRaises(exception.BayModelNotFound,
                          self.dbapi.destroy_baymodel, 666)

    def test_destroy_baymodel_that_referenced_by_bays(self):
        bm = self._create_test_baymodel()
        bay = utils.create_test_bay(baymodel_id=bm['uuid'])
        self.assertEqual(bm['uuid'], bay.baymodel_id)
        self.assertRaises(exception.BayModelReferenced,
                          self.dbapi.destroy_baymodel, bm['id'])

    def test_create_baymodel_already_exists(self):
        uuid = magnum_utils.generate_uuid()
        self._create_test_baymodel(id=1, uuid=uuid)
        self.assertRaises(exception.BayModelAlreadyExists,
                          self._create_test_baymodel,
                          id=2, uuid=uuid)
