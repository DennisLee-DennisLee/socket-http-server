import socket
import sys
import traceback
import os
import os.path
import mimetypes

def response_ok(body=b"This is a minimal response", mimetype=b"text/plain"):
    """
    returns a basic HTTP response
    Ex:
        response_ok(
            b"<html><h1>Welcome:</h1></html>",
            b"text/html"
        ) ->

        b'''
        HTTP/1.1 200 OK\r\n
        Content-Type: text/html\r\n
        \r\n
        <html><h1>Welcome:</h1></html>\r\n
        '''
    """
    return b"\r\n".join([
        b"HTTP/1.1 200 OK",
        b"Content-Type: " + mimetype,
        b"",
        body
    ])

def response_method_not_allowed():
    """Returns a 405 Method Not Allowed response"""
    return b"\r\n".join([
        b"HTTP/1.1 405 Method Not Allowed",
        b"",
        b"You can't do that on this server!"
    ])

def response_not_found():
    """Returns a 404 Not Found response"""
    return b"HTTP/1.1 404 Not Found\r\n\r\n"

def parse_request(request):
    """
    Given the content of an HTTP request, returns the path of that request.

    This server only handles GET requests, so this method shall raise a
    NotImplementedError if the method of the request is not GET.
    """
    method, path, version = request.split("\r\n")[0].split(" ")
    if method != "GET":
        raise NotImplementedError
    return path

def response_path(path):
    """
    This method should return appropriate content and a mime type.

    If the requested path is a directory, then the content should be a
    plain-text listing of the contents with mimetype `text/plain`.

    If the path is a file, it should return the contents of that file
    and its correct mimetype.

    If the path does not map to a real location, it should raise an
    exception that the server can catch to return a 404 response.

    Ex:
        response_path('/a_web_page.html') -> (b"<html><h1>North Carolina...",
                                            b"text/html")

        response_path('/images/sample_1.png')
                        -> (b"A12BCF...",  # contents of sample_1.png
                            b"image/png")

        response_path('/') -> (b"images/, a_web_page.html, make_type.py,...",
                             b"text/plain")

        response_path('/a_page_that_doesnt_exist.html') -> Raises a NameError

    """
    path_parts = path.split("/")
    full_path = os.path.join(os.getcwd(), "webroot", *path_parts)
    if os.path.isdir(full_path):
        mime_type = b"text/plain"
        content = "\r\n".join([f.name for f in os.scandir(full_path)]).encode()
    elif os.path.isfile(full_path):
        mime = mimetypes.guess_type(path)[0]
        mime_type = mime.encode()
        if mime.split("/")[0] == "text":
            with open(full_path, "r") as f:
                lines = f.readlines()
                content = "\r\n".join([l.rstrip("\n\r") for l in lines])
                content = (content + "\r\n").encode()
        else:
            with open(full_path, "rb") as f:
                content = f.read()
    else:
        raise NameError

    return content, mime_type

def server(log_buffer=sys.stderr):
    address = ('127.0.0.1', 10000)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("making a server on {0}:{1}".format(*address), file=log_buffer)
    sock.bind(address)
    sock.listen(1)

    try:
        while True:
            print('waiting for a connection', file=log_buffer)
            conn, addr = sock.accept()  # blocking
            try:
                print('connection - {0}:{1}'.format(*addr), file=log_buffer)
                request = ''
                while True:
                    data = conn.recv(1024)
                    request += data.decode('utf8')
                    if '\r\n\r\n' in request:
                        break

                print("Request received:\n{}\n\n".format(request))
                try:
                    path = parse_request(request)
                    body, mimetype = response_path(path)
                    response = response_ok(body, mimetype)
                except NotImplementedError:
                    response = response_method_not_allowed()
                except NameError:
                    response = response_not_found()
                conn.sendall(response)
            except:
                traceback.print_exc()
            finally:
                conn.close() 

    except KeyboardInterrupt:
        sock.close()
        return
    except:
        traceback.print_exc()


if __name__ == '__main__':
    server()
    sys.exit(0)
