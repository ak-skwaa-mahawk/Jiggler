import grpc
import proto.manifold_pb2 as manifold__pb2

class ManifoldInferenceServiceStub(object):
    def __init__(self, channel):
        self.StreamDriftBatch = channel.stream_stream(
                '/tordial.manifold.v1.ManifoldInferenceService/StreamDriftBatch',
                request_serializer=manifold__pb2.DriftBatchRequest.SerializeToString,
                response_deserializer=manifold__pb2.DriftBatchResponse.FromString,
                )

class ManifoldInferenceServiceServicer(object):
    def StreamDriftBatch(self, request_iterator, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_ManifoldInferenceServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'StreamDriftBatch': grpc.stream_stream_rpc_method_handler(
                    servicer.StreamDriftBatch,
                    request_deserializer=manifold__pb2.DriftBatchRequest.FromString,
                    response_serializer=manifold__pb2.DriftBatchResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'tordial.manifold.v1.ManifoldInferenceService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
