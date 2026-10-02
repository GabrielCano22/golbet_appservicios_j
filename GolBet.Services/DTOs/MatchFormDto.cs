using System.ComponentModel.DataAnnotations;
using GolBet.Services.Helpers;

namespace GolBet.Services.DTOs;

public class MatchFormDto
{
    public int Id { get; set; }

    [Display(Name = "Equipo local")]
    [Range(1, int.MaxValue, ErrorMessage = "Seleccione el equipo local")]
    public int HomeTeamId { get; set; }

    [Display(Name = "Equipo visitante")]
    [Range(1, int.MaxValue, ErrorMessage = "Seleccione el equipo visitante")]
    public int AwayTeamId { get; set; }

    [Display(Name = "Fecha y hora (hora de Colombia)")]
    public DateTime Date { get; set; } = DateTime.UtcNow.ToColombiaTime().Date.AddDays(7).AddHours(19);

    [Display(Name = "Cuota local (1)")]
    [Range(typeof(decimal), "1.01", "999.99", ParseLimitsInInvariantCulture = true,
        ErrorMessage = "La cuota debe estar entre 1,01 y 999,99")]
    public decimal HomeOdds { get; set; } = 2.00m;

    [Display(Name = "Cuota empate (X)")]
    [Range(typeof(decimal), "1.01", "999.99", ParseLimitsInInvariantCulture = true,
        ErrorMessage = "La cuota debe estar entre 1,01 y 999,99")]
    public decimal DrawOdds { get; set; } = 3.00m;

    [Display(Name = "Cuota visitante (2)")]
    [Range(typeof(decimal), "1.01", "999.99", ParseLimitsInInvariantCulture = true,
        ErrorMessage = "La cuota debe estar entre 1,01 y 999,99")]
    public decimal AwayOdds { get; set; } = 3.50m;
}
