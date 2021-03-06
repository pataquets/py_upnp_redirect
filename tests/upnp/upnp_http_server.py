import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import logging

service_xmls_ = {}

for c in ['AVTransport', 'ConnectionManager', 'RenderingControl']:
    for n in ['control', 'event', 'scpd']:
        path = '/{}/{}.xml'.format(c, n)
        service_xmls_[path] = (c.lower(), n.lower())

class UPNPHTTPServerHandler(BaseHTTPRequestHandler):
    """
    A HTTP handler that serves the UPnP XML files.
    """

    # Handler for the GET requests
    def do_GET(self):
        logging.info('http server get path:%s' % self.path)

        if self.path == '/upnp_redirect_1_0.xml':
            self.send_response(200)
            self.send_header('Content-type', 'application/xml')
            self.end_headers()
            self.wfile.write(self.get_device_xml().encode())
            return
        elif self.path in service_xmls_:
            c, n = service_xmls_[self.path]
            desc_xml = self.load_descriptor(c, n)

            if desc_xml:
                self.send_response(200)
                self.send_header('Content-type', 'application/xml')
                self.end_headers()

                self.wfile.write(desc_xml.encode())
                return

        logging.warning('get path not found:%s' % self.path)
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Not found.")
        return

    @staticmethod
    def load_descriptor(category, name):
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        desc_path = os.path.join(BASE_DIR, 'descriptors', category, name + '.xml')

        return open(desc_path).read() if os.path.exists(desc_path) else None

    def do_POST(self):
        # <--- Gets the size of data
        content_length = int(self.headers['Content-Length'])
        # <--- Gets the data itself
        post_data = self.rfile.read(content_length)
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                     str(self.path), str(self.headers), post_data.decode('utf-8'))

    def get_device_xml(self):
        """
        Get the main device descriptor xml file.
        """
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<root configId="9952433" xmlns="urn:schemas-upnp-org:device-1-0" xmlns:dlna="urn:schemas-dlna-org:device-1-0">
  <specVersion>
    <major>1</major>
    <minor>1</minor>
  </specVersion>
  <device>
    <deviceType>urn:schemas-upnp-org:device:MediaRenderer:1</deviceType>
    <friendlyName>{friendly_name}</friendlyName>
    <manufacturer>{manufacturer}</manufacturer>
    <manufacturerURL>{manufacturer_url}</manufacturerURL>
    <modelDescription>{model_description}</modelDescription>
    <modelName>{model_name}</modelName>
    <modelNumber>{model_number}</modelNumber>
    <modelURL>{model_url}</modelURL>
    <serialNumber>{serial_number}</serialNumber>
    <UDN>uuid:{uuid}</UDN>
    <presentationURL>{presentation_url}</presentationURL>
    <dlna:X_DLNADOC xmlns:dlna="urn:schemas-dlna-org:device-1-0">DMR-1.50</dlna:X_DLNADOC>
    <serviceList>
      <service>
        <serviceType>urn:schemas-upnp-org:service:AVTransport:1</serviceType>
        <serviceId>urn:upnp-org:serviceId:AVTransport</serviceId>
        <controlURL>/AVTransport/control.xml</controlURL>
        <eventSubURL>/AVTransport/event.xml</eventSubURL>
        <SCPDURL>/AVTransport/scpd.xml</SCPDURL>
      </service>
      <service>
        <serviceType>urn:schemas-upnp-org:service:ConnectionManager:1</serviceType>
        <serviceId>urn:upnp-org:serviceId:ConnectionManager</serviceId>
        <SCPDURL>/ConnectionManager/scpd.xml</SCPDURL>
        <controlURL>/ConnectionManager/control.xml</controlURL>
        <eventSubURL>/ConnectionManager/event.xml</eventSubURL>
      </service>
      <service>
        <serviceType>urn:schemas-upnp-org:service:RenderingControl:1</serviceType>
        <serviceId>urn:upnp-org:serviceId:RenderingControl</serviceId>
        <SCPDURL>/RenderingControl/scpd.xml</SCPDURL>
        <controlURL>/RenderingControl/control.xml</controlURL>
        <eventSubURL>/RenderingControl/event.xml</eventSubURL>
      </service>
    </serviceList>
  </device>
</root>"""
        return xml.format(friendly_name=self.server.friendly_name,
                          manufacturer=self.server.manufacturer,
                          manufacturer_url=self.server.manufacturer_url,
                          model_description=self.server.model_description,
                          model_name=self.server.model_name,
                          model_number=self.server.model_number,
                          model_url=self.server.model_url,
                          serial_number=self.server.serial_number,
                          uuid=self.server.uuid,
                          presentation_url=self.server.presentation_url)



class UPNPHTTPServerBase(HTTPServer):
    """
    A simple HTTP server that knows the information about a UPnP device.
    """
    def __init__(self, server_address, request_handler_class):
        HTTPServer.__init__(self, server_address, request_handler_class)
        self.port = None
        self.friendly_name = None
        self.manufacturer = None
        self.manufacturer_url = None
        self.model_description = None
        self.model_name = None
        self.model_url = None
        self.serial_number = None
        self.uuid = None
        self.presentation_url = None


class UPNPHTTPServer(threading.Thread):
    """
    A thread that runs UPNPHTTPServerBase.
    """

    def __init__(self, port, friendly_name, manufacturer, manufacturer_url, model_description, model_name,
                 model_number, model_url, serial_number, uuid, presentation_url):
        threading.Thread.__init__(self, daemon=True)
        self.server = UPNPHTTPServerBase(('', port), UPNPHTTPServerHandler)
        self.server.port = self.server.server_port
        self.server.friendly_name = friendly_name
        self.server.manufacturer = manufacturer
        self.server.manufacturer_url = manufacturer_url
        self.server.model_description = model_description
        self.server.model_name = model_name
        self.server.model_number = model_number
        self.server.model_url = model_url
        self.server.serial_number = serial_number
        self.server.uuid = uuid
        self.server.presentation_url = presentation_url

    def run(self):
        self.server.serve_forever()
