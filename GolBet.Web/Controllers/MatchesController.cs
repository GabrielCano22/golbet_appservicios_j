//GolBet.Web/Controllers/MatchesController.cs
using GolBet.Entities.Enums;
using GolBet.Services.DTOs;
using GolBet.Services.Interfaces;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.AspNetCore.Authorization;
using GolBet.Repositories.Data;

namespace GolBet.Web.Controllers;

public class MatchesController : Controller
{
    private readonly IMatchService _matchService;
    private readonly ITeamService _teamService;

    public MatchesController(IMatchService matchService, ITeamService teamService)
    {
        _matchService = matchService;
        _teamService = teamService;
    }

    // GET /Matches            -> all matches
    // GET /Matches?status=Scheduled -> filtered board
    // GET /Matches?status=Scheduled&search=nacional -> filtered board by team
    public async Task<IActionResult> Index(MatchStatus? status, string? search)
    {
        ViewBag.CurrentStatus = status;
        ViewBag.CurrentSearch = search;
        var board = await _matchService.GetBoardAsync(status, search);
        return View(board);
    }

    // GET /Matches/Detail/3
    public async Task<IActionResult> Detail(int id)
    {
        var match = await _matchService.GetDetailAsync(id);
        if (match is null) return NotFound();

        return View(match);
    }

    [Authorize(Roles = DbSeeder.AdminRole)]
    public async Task<IActionResult> Create()
    {
        await LoadTeamsAsync();
        return View(new MatchFormDto());
    }

    [HttpPost, ValidateAntiForgeryToken]
    [Authorize(Roles = DbSeeder.AdminRole)]
    public async Task<IActionResult> Create(MatchFormDto dto)
    {
        dto.Id = 0;
        if (ModelState.IsValid)
        {
            try
            {
                await _matchService.CreateAsync(dto);
                TempData["Success"] = "Partido creado correctamente.";
                return RedirectToAction(nameof(Index));
            }
            catch (InvalidOperationException ex)
            {
                ModelState.AddModelError(string.Empty, ex.Message);
            }
        }
        await LoadTeamsAsync();
        return View(dto);
    }

    [Authorize(Roles = DbSeeder.AdminRole)]
    public async Task<IActionResult> Edit(int id)
    {
        var dto = await _matchService.GetForEditAsync(id);
        if (dto is null) return NotFound();
        await LoadTeamsAsync();
        return View(dto);
    }

    [HttpPost, ValidateAntiForgeryToken]
    [Authorize(Roles = DbSeeder.AdminRole)]
    public async Task<IActionResult> Edit(MatchFormDto dto)
    {
        if (ModelState.IsValid)
        {
            try
            {
                await _matchService.UpdateAsync(dto);
                TempData["Success"] = "Partido actualizado.";
                return RedirectToAction(nameof(Index));
            }
            catch (KeyNotFoundException) { return NotFound(); }
            catch (InvalidOperationException ex)
            {
                ModelState.AddModelError(string.Empty, ex.Message);
            }
        }
        await LoadTeamsAsync();
        return View(dto);
    }

    [HttpPost, ValidateAntiForgeryToken]
    [Authorize(Roles = DbSeeder.AdminRole)]
    public async Task<IActionResult> Deactivate(int id)
    {
        if (await _matchService.GetForEditAsync(id) is null) return NotFound();
        await _matchService.DeactivateAsync(id);
        TempData["Success"] = "Partido desactivado.";
        return RedirectToAction(nameof(Index));
    }

    private async Task LoadTeamsAsync()
        => ViewBag.Teams = new SelectList(await _teamService.GetAllAsync(), "Id", "Name");
}
