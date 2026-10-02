using System.ComponentModel.DataAnnotations;

namespace GolBet.Services.DTOs;

public class TeamFormDto
{
    public int Id { get; set; }

    [Required(ErrorMessage = "El nombre es obligatorio")]
    [MaxLength(80, ErrorMessage = "Máximo 80 caracteres")]
    [Display(Name = "Nombre del equipo")]
    public string Name { get; set; } = null!;

    [Required(ErrorMessage = "La ciudad es obligatoria")]
    [MaxLength(60, ErrorMessage = "Máximo 60 caracteres")]
    [Display(Name = "Ciudad")]
    public string City { get; set; } = null!;

    [Url(ErrorMessage = "Debe ser una URL válida (https://...)")]
    [MaxLength(300, ErrorMessage = "Máximo 300 caracteres")]
    [Display(Name = "URL del escudo (opcional)")]
    public string? CrestUrl { get; set; }
}
