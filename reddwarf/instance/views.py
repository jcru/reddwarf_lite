# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack LLC.
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

import logging
from reddwarf.common import config
from reddwarf.common import utils
from reddwarf.common import wsgi
from reddwarf.common.views import create_links


LOG = logging.getLogger(__name__)


def get_ip_address(addresses):
    if addresses is not None and \
       addresses.get('private') is not None and \
       len(addresses['private']) > 0:
        return [addr.get('addr') for addr in addresses['private']]
    if addresses is not None and\
       addresses.get('usernet') is not None and\
       len(addresses['usernet']) > 0:
        return [addr.get('addr') for addr in addresses['usernet']]


class InstanceView(object):
    """Uses a SimpleInstance."""

    def __init__(self, instance, req=None, add_addresses=False,
                 add_volumes=False):
        self.instance = instance
        self.add_addresses = add_addresses
        self.add_volumes = add_volumes
        self.req = req

    def data(self):
        instance_dict = {
            "id": self.instance.id,
            "name": self.instance.name,
            "status": self.instance.status,
            "links": self._build_links()
        }
        dns_support = config.Config.get("reddwarf_dns_support", 'False')
        if utils.bool_from_string(dns_support):
            instance_dict['hostname'] = self.instance.hostname
        LOG.debug(instance_dict)
        return {"instance": instance_dict}

    def _build_links(self):
        return create_links("instances", self.req, self.instance.id)


class InstanceDetailView(InstanceView):
    """Works with a full-blown instance."""

    def __init__(self, instance, req, add_addresses=False,
                 add_volumes=False):
        super(InstanceDetailView, self).__init__(instance,
                                                 req=req,
                                                 add_volumes=add_volumes)
        self.add_addresses = add_addresses
        self.add_volumes = add_volumes

    def _build_flavor_info(self):
        return {
            "id": self.instance.flavor_id,
            "links": self._build_flavor_links()
        }

    def data(self):
        result = super(InstanceDetailView, self).data()
        result['instance']['created'] = self.instance.created
        result['instance']['flavor'] = self._build_flavor_info()
        result['instance']['updated'] = self.instance.updated
        if self.add_volumes:
            result['instance']['volume'] = {
                'size':self.instance.volume_size
            }
        if self.add_addresses:
            ip = get_ip_address(self.instance.addresses)
            if ip is not None and len(ip) > 0:
                result['instance']['ip'] = ip
        return result

    def _build_flavor_links(self):
        return create_links("flavors", self.req,
                            self.instance.flavor_id)


class InstancesView(object):
    """Shows a list of SimpleInstance objects."""

    def __init__(self, instances, req=None):
        self.instances = instances
        self.req = req

    def data(self):
        data = []
        # These are model instances
        for instance in self.instances:
            instance_data = self.data_for_instance(instance)
            # Remove the hostname from details
            instance_data.pop('hostname', None)
            data.append(instance_data)
        return {'instances': data}

    def data_for_instance(self, instance):
        view = InstanceView(instance, req=self.req)
        return view.data()['instance']


class InstancesDetailView(InstancesView):

    def __init__(self, instances, req=None, add_addresses=False,
                 add_volumes=True):
        super(InstancesDetailView, self).__init__(instances, req)
        self.add_addresses = add_addresses
        self.add_volumes = add_volumes

    def data_for_instance(self, instance):
        return InstanceDetailView(instance, req=self.req,
                               add_addresses=self.add_addresses,
                               add_volumes=self.add_volumes).data()['instance']
