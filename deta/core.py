"""
Core module for the wup package.
"""

class Wup:
    """Base class for wup operations."""
    
    def __init__(self, name: str, dosage: str = None):
        """
        Initialize a Wup instance.
        
        Args:
            name: The name of the wup
            dosage: The dosage information (optional)
        """
        self.name = name
        self.dosage = dosage
    
    def __repr__(self):
        return f"Wup(name='{self.name}', dosage='{self.dosage}')"
    
    def get_info(self) -> str:
        """Return wup information."""
        if self.dosage:
            return f"{self.name} - {self.dosage}"
        return self.name
