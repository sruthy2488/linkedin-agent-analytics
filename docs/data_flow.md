\# LinkedIn Agent Analytics – End-to-End Data Flow



\## 1. Architecture Overview



The LinkedIn Agent Analytics platform follows a layered data architecture:



LinkedIn Agent

&#x20;     |

&#x20;     v

Raw Data / API Source

&#x20;     |

&#x20;     v

Ingestion Pipeline

&#x20;     |

&#x20;     +----> Validation

&#x20;     |        |

&#x20;     |        +---- Invalid Records --> Dead Letter Table

&#x20;     |

&#x20;     v

Staging Layer

(stg\_leads)

&#x20;     |

&#x20;     v

Star Schema / Warehouse

&#x20;     |

&#x20;     +----> dim\_agent

&#x20;     |

&#x20;     +----> dim\_lead\_status

&#x20;     |

&#x20;     +----> dim\_date

&#x20;     |

&#x20;     +----> fct\_leads\_star

&#x20;     |

&#x20;     v

Analytics Layer

&#x20;     |

&#x20;     +----> Lead Funnel

&#x20;     +----> Lead Status

&#x20;     +----> Agent Performance

&#x20;     |

&#x20;     v

Data Quality

&#x20;     |

&#x20;     +----> DQ Score

&#x20;     +----> DQ History

&#x20;     |

&#x20;     v

Advanced Risk Model

&#x20;     |

&#x20;     +----> Risk Score

&#x20;     +----> Risk Level

&#x20;     +----> Capacity Recommendation

&#x20;     |

&#x20;     v

Presentation / Dashboard Layer

