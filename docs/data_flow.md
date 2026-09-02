# LinkedIn Agent Analytics â€“ End-to-End Data Flow



## 1. Architecture Overview



The LinkedIn Agent Analytics platform follows a layered data architecture:



```text

LinkedIn Agent

     |

     v

Raw Data / API Source

     |

     v

Ingestion Pipeline

     |

     +----> Validation

     |        |

     |        +---- Invalid Records --> Dead Letter Table

     |

     v

Staging Layer

(stg_leads)

     |

     v

Star Schema / Warehouse

     |

     +----> dim_agent

     |

     +----> dim_lead_status

     |

     +----> dim_date

     |

     +----> fct_leads_star

     |

     v

Analytics Layer

     |

     +----> analytics_lead_funnel

     |

     +----> analytics_lead_status

     |

     +----> analytics_agent_performance

     |

     v

Data Quality Layer

     |

     +----> DQ Score

     |

     +----> DQ History

     |

     v

Advanced Risk Model

     |

     +----> Risk Score

     |

     +----> Risk Level

     |

     +----> Capacity Recommendation

     |

     v

Presentation / Dashboard Layer

