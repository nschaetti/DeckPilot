import React from "react";
import Link from "@docusaurus/Link";

export default function HeroGradient() {
  return (
    <header className="hero hero-gradient">
        <div className="container hero-inner">
            <div className="heroLeft">
                <h1 className="hero-title">DeckPilot</h1>
                <p className="hero-subtitle">The fully programmable Stream Deck controller.</p>

                <div className="hero-buttons">
                    <Link className="button button--primary" to="/docs">
                      Get Started
                    </Link>
                    <Link className="button button--secondary" to="https://github.com/schaettinils/DeckPilot">
                      GitHub
                    </Link>
                </div>
            </div>

            <div className="hero-right">
                <img src="/img/deckpilot.png" alt="DeckPilot Screenshot" />
            </div>
        </div>
    </header>
  );
}
