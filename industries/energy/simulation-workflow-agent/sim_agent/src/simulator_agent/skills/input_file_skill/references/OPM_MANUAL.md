# OPM Flow Manual Reference

This skill works with OPM Flow DATA files. For detailed keyword documentation, refer to:

1. **OPM Manual**: The official OPM Flow manual (PDF) contains complete keyword reference
2. **OPM Examples**: Example DATA files in the knowledge base demonstrate proper usage

## Common Keywords Used by This Skill

### WCONINJE (Well Control - Injection)
Controls injection well rates and constraints.

### WCONPROD (Well Control - Production)
Controls production well rates and constraints.

### WELLDIMS (Well Dimensions)
Defines maximum number of wells and related parameters.

### COMPDAT (Completion Data)
Defines well connections to the grid.

### WELSPECS (Well Specification)
Defines well names, locations, and types.

## Section Structure

OPM DATA files typically contain these sections:

- **RUNSPEC**: Runtime specifications
- **GRID**: Grid definition
- **PROPS**: Rock and fluid properties
- **SOLUTION**: Initial conditions
- **SUMMARY**: Output requests
- **SCHEDULE**: Well schedule and controls

## Validation Rules

The skill validates:
- Required sections are present
- Keywords are properly terminated with `/`
- Basic syntax consistency

For full validation, run the simulation; success or failure indicates whether the DATA file is valid.

