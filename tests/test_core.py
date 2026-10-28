import json
import struct
import wave
import pytest
from mix2vst.core import Note, create_sfz, parse_notes
from mix2vst.providers import Cue, ModelNotConfigured, PointAndPlayAdapter

def sample(folder, name):
    with wave.open(str(folder / name), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(44100)
        w.writeframes(struct.pack('<'+'h'*200, *([0]*200)))

def test_generate_sfz_and_sha(tmp_path):
    src = tmp_path/'src'; src.mkdir()
    sample(src, 'C4.wav'); sample(src, 'G4.wav')
    out = tmp_path/'out'
    manifest = create_sfz(src, out, [Note(60,64,'C4.wav',0.8), Note(67,100,'G4.wav',0.9)],name='demo')
    assert len(manifest['notes']) == 2
    assert '<region>' in (out/'demo.sfz').read_text()
    assert (out/'Samples'/'C4.wav').is_file()
    assert len(manifest['notes'][0]['sha256']) == 64

def test_reject_path_traversal(tmp_path):
    with pytest.raises(ValueError):
        Note(60,64,'../secret.wav').validate(tmp_path)

def test_duplicate_zone(tmp_path):
    sample(tmp_path, 'C4.wav')
    with pytest.raises(ValueError):
        create_sfz(tmp_path, tmp_path/'out', [Note(60,64,'C4.wav'),Note(60,64,'C4.wav')])

def test_cue_requires_existing_audio(tmp_path):
    with pytest.raises(FileNotFoundError):
        Cue(tmp_path/'missing.wav','violin',0,4).validate()

def test_provider_no_false_success(tmp_path):
    sample(tmp_path, 'mix.wav')
    with pytest.raises(ModelNotConfigured):
        PointAndPlayAdapter().generate(Cue(tmp_path/'mix.wav','guitar',0,4),[60],[100],tmp_path/'out')

def test_json_notes(tmp_path):
    j=tmp_path/'notes.json';j.write_text(json.dumps([{'midi':60,'velocity':64,'wav':'C4.wav'}]))
    assert parse_notes(j)[0].midi==60
