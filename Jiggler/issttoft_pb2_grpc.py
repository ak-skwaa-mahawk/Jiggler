import grpc
import issttoft_pb2

class InferenceServiceServicer(object):
    def Handshake(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def StreamTelemetry(self, request_iterator, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_InferenceServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
        'Handshake': grpc.unary_unary_rpc_method_handler(
            servicer.Handshake,
            # Pass explicit serialization/deserialization hooks
            request_deserializer=issttoft_pb2.HandshakeRequest.FromString,
            response_serializer=lambda x: x.SerializeToString(),
        ),
        'StreamTelemetry': grpc.stream_stream_rpc_method_handler(
            servicer.StreamTelemetry,
            request_deserializer=issttoft_pb2.HandshakeRequest.FromString,
            response_serializer=lambda x: x.SerializeToString(),
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        'issttoft.InferenceService', rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))

class InferenceServiceStub(object):
    def __init__(self, channel):
        self.Handshake = channel.unary_unary(
            '/issttoft.InferenceService/Handshake',
            request_serializer=lambda x: x.SerializeToString(),
            response_deserializer=issttoft_pb2.HandshakeResponse.FromString,
        )
        self.StreamTelemetry = channel.stream_stream(
            '/issttoft.InferenceService/StreamTelemetry',
            request_serializer=lambda x: x.SerializeToString(),
            response_deserializer=issttoft_pb2.TelemetryAck.FromString,
        )
