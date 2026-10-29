"""Beaches in the 19 Degrees picker, north to south on each coast.
key, name, beach lat/lon (for today's reading from Open-Meteo), the HadISST sea patch to start from
(the fetcher steps offshore if that 1° cell is land), and the coast ("east" or "west")."""
BEACHES = [
 ("goldcoast", "Gold Coast", -28.00, 153.43, -28.0, 153.9, "east"),
 ("byron", "Byron Bay", -28.64, 153.62, -28.6, 154.0, "east"),
 ("newcastle", "Newcastle", -32.93, 151.78, -32.9, 152.3, "east"),
 ("sydney", "Sydney", -33.89, 151.28, -33.9, 151.5, "east"),
 ("wollongong", "Wollongong", -34.43, 150.90, -34.4, 151.3, "east"),
 ("eden", "Eden", -37.07, 149.91, -37.1, 150.4, "east"),
 ("exmouth", "Exmouth", -21.93, 114.13, -21.5, 113.5, "west"),
 ("geraldton", "Geraldton", -28.77, 114.61, -28.5, 113.5, "west"),
 ("perth", "Perth", -31.99, 115.75, -31.9, 115.2, "west"),
 ("mandurah", "Mandurah", -32.53, 115.72, -32.5, 115.2, "west"),
 ("margaret", "Margaret River", -33.95, 114.99, -33.9, 114.5, "west"),
 ("albany", "Albany", -35.02, 117.88, -35.5, 117.9, "west"),
]
