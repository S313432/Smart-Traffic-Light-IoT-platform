import json
import cherrypy
import datetime
import requests


class ServiceCatalogManager(object):

    def __init__(self):
        self.settings = "service_settings.json"
        self.cat = json.load(open(self.settings))

    exposed = True

    def GET(self, *uri, **parameters):
        if len(uri) == 1:
            self.settings = "service_settings.json"
            self.cat = json.load(open(self.settings))
            if uri[0] == 'res_cat':
                return json.dumps(self.cat["resource_catalogs"])
            elif uri[0] == 'one_res_cat':
                results = self.cat['resource_catalogs'][len(self.cat["resource_catalogs"]) - 1]
                return json.dumps(results)
            elif uri[0] == 'broker':
                output_website = self.cat['broker']
                output_port = self.getBrokerPort()
                output = {
                    'broker_port': output_port,
                    'broker': output_website,
                }
                print(output)
                return json.dumps(output)
            elif uri[0] == 'base_topic':
                return json.dumps(self.cat["base_topic"])
        else:
            error_string = "incorrect URI or PARAMETERS URI" + str(len(uri)) + "PAR" + str(len(parameters))
            raise cherrypy.HTTPError(400, error_string)

    def PUT(self, *uri, **params):
        if uri[0] == 'registerResourceCatalog':
            body = cherrypy.request.body.read()
            json_body = json.loads(body)
            ip = json_body["ip_address"]
            port = json_body["ip_port"]
            try:
                for item in self.cat["resource_catalogs"]:
                    if ip == item["ip_address"]:
                        if port == item["ip_port"]:
                            resourcesList = self.cat["resource_catalogs"]
                            resourcesList.remove(item)
                            resourcesList.append(json_body)
                            self.cat["resource_catalogs"] = resourcesList
                            file = open(self.settings, "w")
                            json.dump(self.cat, file)
                            return 'Registered successfully'

                self.cat["resource_catalogs"].append(json_body)
                file = open(self.settings, "w")
                json.dump(self.cat, file)
                return 'Registered successfully'
            except:
                return 'An error occurred during registration of Resource Catalog'

    def getPort(self):
        return self.cat['ip_port']

    def getBrokerPort(self):
        return self.cat['broker_port']


if __name__ == "__main__":
    service_info = json.load(open('service_catalog_info.json'))
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
        }
    }
    cherrypy.tree.mount(ServiceCatalogManager(), '/', conf)
    cherrypy.config.update(conf)
    cherrypy.config.update({'server.socket_host': service_info['ip_address_service']})
    cherrypy.config.update({"server.socket_port": ServiceCatalogManager().getPort()})
    cherrypy.engine.start()
    cherrypy.engine.block()
