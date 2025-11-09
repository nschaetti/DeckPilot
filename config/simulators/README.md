# Simulator Configurations

Each TOML file in this directory describes the virtual Stream Decks that the
DeckPilot simulator should expose. Use the `--simulator-config` CLI argument
to point DeckPilot at one of these files, for example:

```sh
python -m deckpilot \
  --config config/config.toml \
  --use-simulator \
  --simulator-config config/simulators/original.toml
```

The default configuration (Original, 3×5) is automatically selected when the
`--simulator-config` option is omitted.
