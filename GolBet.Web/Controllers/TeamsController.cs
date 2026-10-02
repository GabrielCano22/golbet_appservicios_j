using GolBet.Services.DTOs;
using GolBet.Services.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace GolBet.Web.Controllers;

public class TeamsController : Controller
{
    private readonly ITeamService _teamService;

    public TeamsController(ITeamService teamService) => _teamService = teamService;

    public async Task<IActionResult> Index() => View(await _teamService.GetAllAsync());

    public IActionResult Create() => View(new TeamFormDto());

    [HttpPost, ValidateAntiForgeryToken]
    public async Task<IActionResult> Create(TeamFormDto dto)
    {
        dto.Id = 0;
        if (!ModelState.IsValid) return View(dto);
        await _teamService.CreateAsync(dto);
        TempData["Success"] = $"Equipo «{dto.Name}» creado correctamente.";
        return RedirectToAction(nameof(Index));
    }

    public async Task<IActionResult> Edit(int id)
    {
        var dto = await _teamService.GetForEditAsync(id);
        return dto is null ? NotFound() : View(dto);
    }

    [HttpPost, ValidateAntiForgeryToken]
    public async Task<IActionResult> Edit(TeamFormDto dto)
    {
        if (!ModelState.IsValid) return View(dto);
        try
        {
            await _teamService.UpdateAsync(dto);
        }
        catch (KeyNotFoundException) { return NotFound(); }
        TempData["Success"] = $"Equipo «{dto.Name}» actualizado.";
        return RedirectToAction(nameof(Index));
    }

    [HttpPost, ValidateAntiForgeryToken]
    public async Task<IActionResult> Deactivate(int id)
    {
        if (await _teamService.GetForEditAsync(id) is null) return NotFound();
        await _teamService.DeactivateAsync(id);
        TempData["Success"] = "Equipo desactivado.";
        return RedirectToAction(nameof(Index));
    }
}
