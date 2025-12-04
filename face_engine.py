from mtcnn import MTCNN
from keras_facenet import FaceNet

_detector = None
_embedder = None

def get_detector():
    global _detector
    if _detector is None:
        _detector = MTCNN()
    return _detector

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = FaceNet()
    return _embedder


def shutdown():
    """Attempt to release detector/embedder resources and clear TF session."""
    global _detector, _embedder
    try:
        _detector = None
    except Exception:
        pass
    try:
        # try to clear keras/tf session to release file handles
        try:
            import importlib
            K = importlib.import_module('tensorflow.keras.backend')
            try:
                K.clear_session()
            except Exception:
                pass
        except Exception:
            try:
                import importlib
                K2 = importlib.import_module('keras.backend')
                try:
                    K2.clear_session()
                except Exception:
                    pass
            except Exception:
                pass
    except Exception:
        pass
    try:
        _embedder = None
    except Exception:
        pass
