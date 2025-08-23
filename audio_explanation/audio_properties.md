
# Digital Audio Properties & Concepts

## How Audio is Stored and Processed

- **Analog-to-Digital Conversion (ADC):** A physical electronic component that converts analog sound (like a microphone signal or vinyl record) into digital data by sampling the signal at regular intervals and quantizing the amplitude. This process produces PCM data.

- **PCM (Pulse Code Modulation):** Both a process and a format. PCM is the standard method for converting analog audio to digital by sampling and quantizing. The resulting digital data (PCM) is an uncompressed stream of samples representing the original sound wave. CDs store audio in PCM format (16-bit, 44.1 kHz, stereo).

- **CDs vs. Vinyl:**
	- **Vinyl:** Stores analog audio as continuous grooves. The groove shape directly represents the sound wave. Playback uses a needle to physically trace the groove.
	- **CDs:** Store digital audio as microscopic pits and lands encoding binary data (0s and 1s). A laser reads these patterns, which are decoded as PCM digital audio.

- **Ripping CDs:** Ripping software reads the digital PCM data directly from the CD and saves it as a file (WAV, FLAC, MP3, etc.). No analog conversion is involved—it's a direct digital copy.

- **Codecs:** Short for coder-decoder. Codecs are software or hardware that compress and decompress digital audio. When ripping CDs, codecs are used if you want to save the audio in a compressed format (like MP3, FLAC, or ALAC) instead of uncompressed PCM (WAV).

## Key Audio Properties

- **Sample Rate:** Number of times per second the audio signal is measured (Hz). Determines the highest frequency that can be captured. CD quality is 44.1 kHz (captures up to 22.05 kHz).
- **Bit Depth:** Number of bits per sample. Determines amplitude precision and dynamic range. 16-bit audio (CD quality) allows for 65,536 levels and ~96 dB dynamic range.
- **Channels:** Number of separate audio streams (1 = mono, 2 = stereo).
- **Bitrate:** Data processed per second: sample rate × bit depth × channels (bits per second).

## Practical Audio Quality

- **CD Quality (44.1 kHz, 16-bit, stereo):** Covers the full range of human hearing (20 Hz–20 kHz) and provides more dynamic range than most people can discern. Bitrate: 1,411 kbps.
- **Higher Sample Rates/Bit Depths:** Used in professional audio production for editing headroom, not needed for typical listening.

## Summary

- ADCs convert analog sound to digital PCM data.
- CDs store digital PCM audio; vinyl stores analog audio in grooves.
- Ripping CDs is a direct digital copy; codecs are used for compression.
- 44.1 kHz/16-bit is the practical maximum for playback quality; higher values are for production.
