import React from "react";
import { PageHead } from "../ui/primitives";

/** Pulse (home). Built out in phase 3. */
export const PulsePage: React.FC = () => (
  <div className="view" data-testid="page-pulse">
    <PageHead title="What's heating up in AI research" sub="AAAI and IJCAI, 2021–2025" />
  </div>
);
