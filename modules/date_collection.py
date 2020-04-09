import json, math, operator
from datetime import date, timedelta
from dateutil import rrule
from functools import reduce


def first_morning(checkout_date, nights):
    """Returns the date one day after checkin."""
    return(checkout_date - timedelta(days=(nights-1)))


class DateCollection:
    """Manages a range of dates with a location assigned to each."""
    
    COORDINATES_PATH = "data/coordinates.json"
    
    def __init__(self, start_date, end_date, default_location=None):
        """Initialize a DateCollection."""
        
        with open(self.COORDINATES_PATH, 'r', encoding="utf-8") as f:
            self.location_coordinates = json.load(f)
        
        default_value = None if default_location == None else {
            'city': default_location,
            'coordinates': self._coordinates(default_location)}
        # Create dictionary of dates with locations set to None by default:
        self.locations = {d:default_value for d in self._inclusive_date_range(
            start_date, end_date)}

    def _coordinates(self, location):
        """Returns the coordinates for a location."""
        location_list = location.split("/")
        try:
            return(reduce(operator.getitem, location_list,
                self.location_coordinates))
        except KeyError as err:
            print(f"\nCould not find coordinates for:")
            print(location)
            print(f"\nPlease add it to {self.COORDINATES_PATH}.\n")
            raise SystemExit()

    def _inclusive_date_range(self, start_date, end_date):
        """Returns a list of date objects in the given range."""
        return([d.date() for d in list(rrule.rrule(rrule.DAILY,
            dtstart=start_date, until=end_date))])

    def set_location(self, checkout_date, nights, location):
        """ Sets the locations for the dates in a given hotel stay."""
        dates = self._inclusive_date_range(
            first_morning(checkout_date, nights),
            checkout_date)
        
        for day in dates:
            if day in self.locations.keys():
                self.locations[day] = {
                    'city': location,
                    'coordinates': self._coordinates(location)}


class DateDistanceCollection(DateCollection):
    """Manages a range of dates with a distance assigned to each."""
    
    EARTH_MEAN_RADIUS = 3958.7613 # miles
    DEG_TO_RAD = math.pi / 180

    def __init__(self, start_year, end_year, home_location):
        """Initialize a DateDistanceCollection."""
        
        start_date = date(start_year, 1, 1)
        end_date = date(end_year, 12, 31)

        super().__init__(start_date, end_date, home_location)
        self.home_coordinates = self._coordinates(home_location)

        # Add distances to locations dictionary:
        for day, loc in self.locations.items():
            self.locations[day] = {**loc, 'distance': 0.0}
            
   
    def _home_distance(self, location):
        """Returns the distance from home to the provided location.
        
        The Haversine formula is used to calculate the distance.
        """
        location_coordinates = self._coordinates(location)
        phi_1 = self.home_coordinates[0] * self.DEG_TO_RAD
        phi_2 = location_coordinates[0] * self.DEG_TO_RAD
        delta_phi = (
            (location_coordinates[0] - self.home_coordinates[0])
            * self.DEG_TO_RAD)
        delta_lambda = (
            (location_coordinates[1] - self.home_coordinates[1])
            * self.DEG_TO_RAD)
        a = (math.sin(delta_phi/2)**2
            + math.cos(phi_1)
            * math.cos(phi_2)
            * math.sin(delta_lambda/2)**2)
        distance = (2
            * self.EARTH_MEAN_RADIUS
            * math.atan2(math.sqrt(a), math.sqrt(1-a)))
        return distance

    def set_location(self, checkout_date, nights, location):
        """ Sets locations and distances.
        
        Sets the location, coordinates, and distances for the dates in a
        given hotel stay.
        """
        dates = self._inclusive_date_range(
            first_morning(checkout_date, nights),
            checkout_date)
        distance = self._home_distance(location)
        
        for day in dates:
            if day in self.locations.keys():
                self.locations[day] = {
                    'city': location,
                    'coordinates': self._coordinates(location),
                    'distance': distance}