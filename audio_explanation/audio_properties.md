# Audio Properties Explained

## Key Properties

- **Sample Rate**: The number of times per second the audio signal is measured (samples per second, Hz). Determines the highest frequency that can be captured. For example, 44.1 kHz sample rate can capture frequencies up to 22.05 kHz (the Nyquist frequency).

- **Bit Depth**: The number of bits used to represent each audio sample. Determines the precision of amplitude measurements and the dynamic range. 16-bit audio allows for 65,536 possible amplitude levels per sample, providing a dynamic range of about 96 dB.

- **Channels**: The number of separate audio streams (e.g., 1 for mono, 2 for stereo).

- **Bitrate**: The amount of data processed per second, calculated as sample rate × bit depth × number of channels (bits per second).

## Theoretical Maximum for Human Hearing

- The standard for transparent audio quality is 44.1 kHz sample rate and 16-bit depth (CD quality).
- This covers the full range of human hearing (20 Hz–20 kHz) and provides more dynamic range than the ear can typically discern.
- Bitrate for CD quality stereo: 44,100 × 16 × 2 = 1,411,200 bits per second (1,411 kbps).

## Why Go Higher?
- Higher sample rates (e.g., 48 kHz, 96 kHz) and bit depths (e.g., 24-bit) are used in professional audio production.
- These higher values provide extra headroom for editing, processing, and effects, reducing the risk of quality loss during production.
- For playback, anything above 44.1 kHz/16-bit is generally unnecessary and results in larger files with no audible benefit for most listeners (homosapiens).

## Summary
- 44.1 kHz sample rate and 16-bit depth are the practical maximums for playback quality.
- Higher values are useful for audio engineers during production, not for typical listening.
