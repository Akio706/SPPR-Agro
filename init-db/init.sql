CREATE TABLE IF NOT EXISTS variety (
    id SERIAL PRIMARY KEY,
    name TEXT,
    seeding INT,
    germination INT,
    tillering INT,
    stem_elongation INT,
    earing INT,
    flowering INT,
    milky_ripeness INT,
    milky_wax_ripeness INT,
    dough_stage INT,
    ripening INT,
    harvesting INT,
    k INT,
    q INT,  
    e INT,
    l Float,
    j INT,
    var_coef Float
);

INSERT INTO variety (name, seeding, germination, tillering, stem_elongation, earing, flowering, milky_ripeness, milky_wax_ripeness, dough_stage, ripening, harvesting, k, q, e, l, j, var_coef)
VALUES
('Annushka', 128, 9, 17, 34, 48, 46, 64, 70, 74, 82, 90, 300, 1900, 25, 2.20, 2, 0.925925926),
('Gordeya', 128, 9, 17, 33, 47, 46, 64, 68, 74, 82, 90, 300, 1620, 25, 2.20, 2, 0.789473684),
('Luch', 128, 9, 17, 34, 48, 46, 64, 70, 76, 82, 90, 300, 1518, 25, 2.20, 2, 0.739766082),
('Zolotaya', 128, 9, 18, 36, 54, 46, 66, 72, 78, 85, 90, 300, 2052, 25, 2.20, 2, 1);