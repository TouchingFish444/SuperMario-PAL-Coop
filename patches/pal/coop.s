.setcpu "6502"

; PAL Rev A CPU addresses. build_patch.py checks the hooks against the input.
PAL_RESET           = $8000
PAL_RUN_MODE        = $8212
PAL_PLAYER_TILES    = $EE1E
PAL_LUIGI_COLORS    = $85DC
PAL_FIRE_COLORS     = $85DF
PAL_MOVE_PLAYER     = $B329
PAL_SCROLL_RESUME   = $AF96
PAL_SCROLL_SCREEN   = $AFC4
PAL_STOP_SCROLL     = $AFFB
PAL_CASTLE_LOOP     = $C092
PAL_RESTORE_MUSIC   = $90ED
PAL_HEAD_COLLISION  = $BCF2
PAL_SOLID_METATILE  = $DF97
PAL_ERASE_ENEMY     = $C99E
PAL_DRAW_FIREBAR    = $ECF4
PAL_FALL_GRAVITY    = $B42B
PAL_COLLECT_COIN    = $DE0D
PAL_CASTLE_AXE      = $DE16
PAL_FLAGPOLE        = $DE49
PAL_VERTICAL_PIPE   = $DEF0
PAL_SIDE_PIPE       = $DDD6
PAL_FRAME           = $09
PAL_GAME_ROUTINE    = $0E
PAL_P1_STATE        = $1D
PAL_P1_X_SPEED      = $57
PAL_P1_PAGE         = $6D
PAL_P1_X            = $86
PAL_P1_Y_SPEED      = $9F
PAL_P1_Y_PAGE       = $B5
PAL_P1_Y            = $CE
PAL_OAM             = $0200
PAL_VRAM_OFFSET     = $0300
PAL_VRAM            = $0301
PAL_TERRAIN         = $0500
PAL_P1_PAD          = $06FC
PAL_P2_PAD          = $06FD
PAL_CAMERA_PAGE     = $071A
PAL_CAMERA_X        = $071C
PAL_SCROLL_LOCK     = $0723
PAL_PLAYER_SCROLL   = $06FF
PAL_PLATFORM_SCROLL = $03A1
PAL_AREA_TYPE       = $074E
PAL_P1_SMALL        = $0754
PAL_TIME_EXPIRED    = $0759
PAL_AREA_POINTER    = $0750
PAL_SWIMMING        = $0704
PAL_CHANGE_AREA_TIMER = $06DE
PAL_MODE            = $0770
PAL_MODE_TASK       = $0772
PAL_VRAM_CONTROL    = $0773
PAL_TWO_PLAYERS     = $077A
PAL_SELECT_TIMER    = $0780
PAL_BLOCK_TIMER     = $0784
PAL_INJURY_TIMER    = $079E
PAL_CURRENT_PLAYER  = $0753
PAL_PLAYER_STATUS   = $0756
PAL_PLAYER_COINS    = $075E
PAL_CROUCHING       = $0714
PAL_POWER_UP_TYPE   = $39
PAL_SOUND_POWER_UP  = $FE
PAL_LUIGI_SCORE     = $07E3
PAL_MARIO_SCORE     = $07DD
PAL_ENEMY_FLAGS     = $0F
PAL_ENEMY_IDS       = $16
PAL_ENEMY_STATES    = $1E
PAL_ENEMY_DIRECTION = $46
PAL_ENEMY_X_SPEED   = $58
PAL_ENEMY_X         = $87
PAL_ENEMY_Y_PAGE    = $B6
PAL_ENEMY_Y         = $CF
PAL_ENEMY_BOX       = $04B0
PAL_ENEMY_TIMER     = $0796

MMC3_SELECT         = $8000
MMC3_BANK           = $8001
MMC3_MIRROR         = $A000
MMC3_RAM            = $A001
MMC3_IRQ_DISABLE    = $E000

; Volatile MMC3 PRG RAM. The overlay executes at $6000-$6FFF, leaving its
; original bank visible so calls can reach every stock PAL engine routine.
p2_active           = $7000
p2_x                = $7001
p2_page             = $7002
p2_y                = $7003
p2_delta_y          = $7004
p2_grounded         = $7005
title_previous_a    = $7006
p2_pad              = $7007
p2_facing           = $7008
p2_screen_x         = $7009
p2_walk_steps       = $700A
p2_direction        = $700B
p2_new_x            = $700C
p2_new_page         = $700D
p2_new_y            = $700E
p2_vertical_steps   = $700F
p2_oam_slots        = $7030
p2_tiles            = $7014
p2_walking          = $7015
probe_x             = $7016
probe_page          = $7017
probe_offset        = $7018
p2_delta_x          = $7019
p2_previous_y       = $701A
p2_invincible       = $701B
enemy_slot          = $701C
p2_top              = $701D
p2_oam_count        = $701E
p2_status           = $701F
p2_hit_top          = $7020
p2_coin_tally       = $7021
p2_prev_ab          = $7022
p2_star             = $7023
p2_block_metatile   = $7024
block_actor_saved   = $7025
p2_fresh_spawn      = $702A
p2_area             = $702B
p2_platform         = $702C
p2_platform_x       = $702D
p2_platform_half    = $702E
p2_firebar_hit      = $702F
p2_actor            = $7040
p1_snapshot         = $7080
camera_budget       = $70A8
terrain_pointer     = $06

CAMERA_FOLLOW_X     = $70
CAMERA_REAR_MARGIN  = 8
CAMERA_MAX_STEP     = 4

.enum Actor
    AB
    UD
    LR
    PreviousAB
    State
    Facing
    Moving
    XSpeed
    XPage
    XPos
    YSpeed
    YPage
    YPos
    XFraction
    YFraction
    YSpeedFraction
    MaximumLeft
    MaximumRight
    CollisionBits
    XScroll
    AbsoluteSpeed
    FrictionHigh
    FrictionLow
    RunningSpeed
    SpeedFraction
    JumpReleaseMin
    JumpOriginPage
    JumpOriginY
    ActiveGravity
    FallGravity
    ChangeSize
    AnimationReload
    AnimationControl
    Crouching
    Small
    AnimationTimer
    JumpTimer
    RunningTimer
    ClimbTimer
    Count
.endenum

.export reset_hook, frame_hook, overlay_boot, player_two_frame, pause_input, draw_firebar
.export coop_scroll, coop_castle_loop

.segment "FIXED"

reset_hook:
    sei
    ldx #7
@set_bank:
    stx MMC3_SELECT
    lda boot_banks,x
    sta MMC3_BANK
    dex
    bpl @set_bank
    inx
    stx MMC3_MIRROR          ; Original vertical mirroring.
    stx MMC3_IRQ_DISABLE
    lda #$80
    sta MMC3_RAM
    jmp overlay_boot

boot_banks:
    ; Keep both original pattern tables and the lower PRG pair in place.
    .byte 0, 2, 4, 5, 6, 7, 2, 1

restore_base_bank:
    lda #6
    sta MMC3_SELECT
    lda #0
    sta MMC3_BANK
    jmp PAL_RESET

.segment "BOOT"

overlay_boot:
    lda #0
    sta $00
    sta $02
    lda #$81
    sta $01
    lda #$60
    sta $03
    ldx #$10
    ldy #0
@copy:
    lda ($00),y
    sta ($02),y
    iny
    bne @copy
    inc $01
    inc $03
    dex
    bne @copy
    stx p2_active
    stx p2_status
    stx p2_star
    stx p2_platform
    stx title_previous_a
    stx p2_coin_tally
    jmp restore_base_bank

.segment "CODE"

frame_hook:
    lda #0
    sta p2_firebar_hit
    jsr normalize_title_input
    jsr PAL_RUN_MODE
    jmp player_two_frame

normalize_title_input:
    lda PAL_MODE
    bne @leave
    lda PAL_MODE_TASK
    cmp #3
    bne @clear_edge
    lda #0
    sta PAL_P2_PAD           ; The room owner controls the title menu.
    lda PAL_P1_PAD
    and #$80
    beq @clear_edge
    lda title_previous_a
    bne @held
    lda #$80
    sta title_previous_a
    lda PAL_P1_PAD
    and #$10
    bne @start
    lda #0
    sta PAL_SELECT_TIMER
    lda #$20                 ; A/K is Select only inside the title menu.
    sta PAL_P1_PAD
    rts
@held:
    lda PAL_P1_PAD
    and #$10
@start:
    sta PAL_P1_PAD           ; Do not invoke the original A+Start shortcut.
    rts
@clear_edge:
    lda #0
    sta title_previous_a
@leave:
    rts

pause_input:
    lda PAL_TWO_PLAYERS
    beq @solo
    lda PAL_P1_PAD
    ora PAL_P2_PAD
    rts
@solo:
    lda PAL_P1_PAD
    rts

; Retain the original scroll and clamp routines. Choose the scroll amount
; from the leading player, bounded by the trailing player's screen position.
coop_scroll:
    lda PAL_TWO_PLAYERS
    beq @stock
    lda PAL_MODE
    cmp #1
    bne @stock
    lda PAL_GAME_ROUTINE
    cmp #8
    beq @check
    cmp #$0A                 ; The original injury handler can still move Mario.
    bne @stock
@check:
    lda p2_active
    beq @stock
    lda p2_area
    cmp PAL_AREA_POINTER
    beq @shared
@stock:
    lda PAL_PLAYER_SCROLL   ; Original bytes displaced by the jump at $AF93.
    jmp PAL_SCROLL_RESUME
@shared:
    lda PAL_PLAYER_SCROLL
    clc
    adc PAL_PLATFORM_SCROLL
    sta PAL_PLAYER_SCROLL
    lda PAL_SCROLL_LOCK
    bne @stop
    jsr screen_position
    bne @stop
    sec
    lda PAL_P1_X
    sbc PAL_CAMERA_X
    tax
    lda PAL_P1_PAGE
    sbc PAL_CAMERA_PAGE
    beq @choose_leader
    bmi @stop
    ldx #$FF                 ; The original edge clamp runs after scrolling.
@choose_leader:
    txa
    ldy p2_screen_x
    cmp p2_screen_x
    bcs @step                ; A is the leader's X, Y is the trailer's X.
    tay
    lda p2_screen_x
@step:
    sec
    sbc #CAMERA_FOLLOW_X
    bcc @stop
    beq @stop
    cmp #CAMERA_MAX_STEP
    bcc @budget
    lda #CAMERA_MAX_STEP
@budget:
    sta camera_budget
    tya
    sec
    sbc #CAMERA_REAR_MARGIN
    bcc @stop
    beq @stop
    cmp camera_budget
    bcc @apply
    lda camera_budget
@apply:
    tay
    jmp PAL_SCROLL_SCREEN
@stop:
    jmp PAL_STOP_SCROLL

; In a castle maze, the base engine rebases its camera and Mario together.
; Keep Luigi at the same screen position on that particular loopback.
coop_castle_loop:
    lda p2_active
    beq @stock
    lda p2_page
    sec
    sbc #4
    sta p2_page
    lda #0
    sta p2_platform
@stock:
    jmp PAL_CASTLE_LOOP

deactivate_partner:
    lda #0
    sta p2_active
    sta p2_platform
    rts

reset_partner_session:
    jsr deactivate_partner
    sta p2_status
    sta p2_star
    sta p2_coin_tally
    rts

player_two_frame:
    lda PAL_MODE
    beq reset_partner_session
    cmp #1
    bne deactivate_partner
    lda PAL_TWO_PLAYERS
    beq reset_partner_session
    lda PAL_MODE_TASK
    cmp #3
    bne deactivate_partner

    lda PAL_GAME_ROUTINE
    cmp #8
    beq @playable
    cmp #$0B                 ; Ordinary enemy death animation.
    beq @revive
    cmp #6                   ; Pit death dispatches the lose-life task.
    beq @revive
    cmp #4                   ; Flagpole / castle walk stay in the current area.
    beq @hold
    cmp #5
    beq @hold
    cmp #9                   ; Mario's grow, injury and fire-flower animations.
    bcs @hold
    jmp deactivate_partner   ; The engine is changing area or placing Mario.
@revive:
    jsr revive_mario_at_luigi
@hold:
    lda p2_active
    beq @hud
    jmp @draw

@playable:
    lda PAL_P2_PAD
    sta p2_pad
    lda p2_active
    beq @place
    lda PAL_AREA_POINTER
    cmp p2_area
    beq @play
@place:
    jsr place_partner
@play:
    jsr screen_position
    bne @hud
    jsr carry_partner
    lda p2_y
    sta p2_previous_y
    lda p2_actor+Actor::PreviousAB
    sta p2_prev_ab
    jsr update_vine_contact
    jsr native_player_motion
    jsr update_body_shape
    jsr walk_partner
    jsr jump_and_fall
    jsr land_on_platform
    lda p2_y
    cmp #$DB
    bcc @encounters
    jsr spawn_partner
@encounters:
    jsr apply_partner_transition
    bcs @draw
    jsr collect_terrain_coin
    jsr collect_power_up
    jsr hit_enemies
    jsr throw_fireball
@draw:
    jsr screen_position
    bne @hud
    jsr draw_partner
@hud:
    jmp update_luigi_hud

spawn_partner:
    lda #0
    sta p2_status
    sta p2_star
place_partner:
    ; Enter a new area or respawn beside the other player.
    lda PAL_AREA_POINTER
    sta p2_area
    lda PAL_P1_PAGE
    sta p2_page
    lda PAL_P1_X
    sta p2_x
    lda PAL_P1_Y
    cmp #$DB
    bcc @store_height
    lda #$50
@store_height:
    sta p2_y
    lda #0
    sta p2_facing
    sta p2_grounded
    sta p2_platform
    ldx #Actor::Count-1
@clear_actor:
    sta p2_actor,x
    dex
    bpl @clear_actor
    lda p2_pad
    and #$C0
    sta p2_actor+Actor::PreviousAB
    ldy #0
    lda PAL_SWIMMING
    beq @gravity
    ldy #5
@gravity:
    lda PAL_FALL_GRAVITY,y
    sta p2_actor+Actor::FallGravity
    lda #1
    sta p2_actor+Actor::Facing
    sta p2_actor+Actor::Moving
    lda #$FF
    sta p2_actor+Actor::CollisionBits
    lda #30
    sta p2_invincible
    lda #1
    sta p2_active
    sta p2_fresh_spawn
    jsr set_partner_size
    jsr screen_position
    bne @return
    lda p2_screen_x
    cmp #$D0
    lda #3
    bcc @separate
    lda #$FD
@separate:
    sta p2_delta_x
    jsr walk_partner
    jsr walk_partner
    jsr walk_partner
    jsr walk_partner
@return:
    rts

screen_position:
    sec
    lda p2_x
    sbc PAL_CAMERA_X
    sta p2_screen_x
    lda p2_page
    sbc PAL_CAMERA_PAGE
    rts                     ; Z iff the high byte of the screen-relative X is zero.

; Invoke the original PAL movement kernel with a complete set of per-player
; physics variables. Its integer displacements go through the partner's
; terrain collision pass before committing either coordinate.
native_player_motion:
    ldx #Actor::Count-1
    ldy #0
@save_mario:
    lda actor_addresses_lo,x
    sta terrain_pointer
    lda actor_addresses_hi,x
    sta terrain_pointer+1
    lda (terrain_pointer),y
    sta p1_snapshot,x
    lda p2_actor,x
    sta (terrain_pointer),y
    dex
    bpl @save_mario

    lda p2_pad
    and #$C0
    sta $0A
    lda p2_pad
    and #$0C
    sta $0B
    lda p2_pad
    and #$03
    sta $0C
    lda p2_x
    sta PAL_P1_X
    lda p2_page
    sta PAL_P1_PAGE
    lda p2_y
    sta PAL_P1_Y
    lda #1
    sta PAL_P1_Y_PAGE
    ldx #2
@timers:
    lda $0781,x
    beq @next_timer
    dec $0781,x
@next_timer:
    dex
    bpl @timers
    jsr PAL_MOVE_PLAYER

    sec
    lda PAL_P1_X
    sbc p2_x
    sta p2_delta_x
    sec
    lda PAL_P1_Y
    sbc p2_y
    sta p2_delta_y
    lda PAL_P1_STATE
    bne @view
    lda #1                   ; Probe under a standing player to detect ledges.
    sta p2_delta_y
@view:
    lda $33
    and #2
    asl
    asl
    asl
    asl
    asl
    sta p2_facing
    lda $0A
    sta $0D
    ldx #Actor::Count-1
    ldy #0
@restore_mario:
    lda actor_addresses_lo,x
    sta terrain_pointer
    lda actor_addresses_hi,x
    sta terrain_pointer+1
    lda (terrain_pointer),y
    sta p2_actor,x
    lda p1_snapshot,x
    sta (terrain_pointer),y
    dex
    bpl @restore_mario
    rts

actor_addresses_lo:
    .lobytes $0A,$0B,$0C,$0D,$1D,$33,$45,$57,$6D,$86,$9F,$B5,$CE,$0400,$0416,$0433
    .lobytes $0450,$0456,$0490,$06FF,$0700,$0701,$0702,$0703,$0705,$0706,$0707,$0708
    .lobytes $0709,$070A,$070B,$070C,$070D,$0714,$0754,$0781,$0782,$0783,$0789
actor_addresses_hi:
    .hibytes $0A,$0B,$0C,$0D,$1D,$33,$45,$57,$6D,$86,$9F,$B5,$CE,$0400,$0416,$0433
    .hibytes $0450,$0456,$0490,$06FF,$0700,$0701,$0702,$0703,$0705,$0706,$0707,$0708
    .hibytes $0709,$070A,$070B,$070C,$070D,$0714,$0754,$0781,$0782,$0783,$0789
    .assert actor_addresses_hi-actor_addresses_lo = Actor::Count, error, "actor field count"

; Both sizes keep the original player origin 32 pixels above the feet.
update_body_shape:
    lda p2_actor+Actor::Small
    ora p2_actor+Actor::Crouching
    beq @standing
    lda #16
@standing:
    sta p2_top
    rts

walk_partner:
    lda #0
    sta p2_walking
    lda p2_delta_x
    bne @direction
    rts
@direction:
    sta p2_direction
    bpl @set_steps
    eor #$FF
    clc
    adc #1
@set_steps:
    sta p2_walk_steps
@step:
    lda p2_direction
    bmi @step_left
    lda p2_screen_x
    cmp #$ED
    bcs @wall
    lda p2_x
    clc
    adc #1
    sta p2_new_x
    lda p2_page
    adc #0
    sta p2_new_page
    lda #14
    bne @probe_edge
@step_left:
    lda p2_screen_x
    beq @wall
    lda p2_x
    sec
    sbc #1
    sta p2_new_x
    lda p2_page
    sbc #0
    sta p2_new_page
    lda #1
@probe_edge:
    clc
    adc p2_new_x
    sta probe_x
    lda p2_new_page
    adc #0
    sta probe_page
    lda p2_y
    clc
    adc p2_top
    adc #2
    jsr solid_tile_at_y
    bcs @wall
    lda p2_y
    clc
    adc #30
    jsr solid_tile_at_y
    bcs @wall
    lda p2_new_x
    sta p2_x
    lda p2_new_page
    sta p2_page
    lda #1
    sta p2_walking
    jsr screen_position
    dec p2_walk_steps
    bne @step
@done:
    rts
@wall:
    lda #0
    sta p2_actor+Actor::XSpeed
    sta p2_actor+Actor::XFraction
    sta p2_actor+Actor::SpeedFraction
    sta p2_actor+Actor::AbsoluteSpeed
    rts

jump_and_fall:
    lda #0
    sta p2_grounded
    lda p2_delta_y
    bne @vertical_motion
    rts
@vertical_motion:
    bmi @rise
    sta p2_vertical_steps
@fall_step:
    lda p2_y
    cmp #$DB
    bcc @fall_pixel
    rts
@fall_pixel:
    clc
    adc #1
    sta p2_new_y
    clc
    adc #31                  ; Bottom of the native 32-pixel player box.
    jsr probe_both_sides
    bcs @land
    lda p2_new_y
    sta p2_y
    dec p2_vertical_steps
    bne @fall_step
    lda p2_actor+Actor::State
    bne @fall_done
    lda #2                   ; Just walked off the edge of a floor.
    sta p2_actor+Actor::State
@fall_done:
    rts
@land:
    cmp #$67                 ; A spring top can propel either player.
    beq @bounce
    cmp #$68
    beq @bounce
    lda #0
    sta p2_platform
    jmp ground_partner
@bounce:
    lda #1
    sta p2_actor+Actor::State
    lda #$70
    sta p2_actor+Actor::ActiveGravity
    lda #$A8
    sta p2_actor+Actor::FallGravity
    lda p2_pad
    bmi @spring_jump
    lda #$F8
    bne @spring_speed
@spring_jump:
    lda #$F2
@spring_speed:
    sta p2_actor+Actor::YSpeed
    rts
@rise:
    eor #$FF
    clc
    adc #1
    sta p2_vertical_steps
@rise_step:
    ldx PAL_SWIMMING
    lda #1
    cpx #0
    beq @rise_limit
    lda #$14                 ; The native swimming ceiling.
@rise_limit:
    cmp p2_y
    bcs @hit_ceiling
    lda p2_y
    sec
    sbc #1
    sta p2_new_y
    clc
    adc p2_top
    sta probe_offset
    lda #8
    jsr probe_player_x       ; The native block strike samples the player's centre.
    bcs @bump
    cmp #$5F                 ; Hidden blocks only react to a strike from below.
    beq @bump
    cmp #$60
    beq @bump
    lda probe_offset
    jsr probe_both_sides
    bcs @hit_ceiling
    lda p2_new_y
    sta p2_y
    dec p2_vertical_steps
    bne @rise_step
    rts
@bump:
    jsr bump_block
@hit_ceiling:
    lda #0
    sta p2_actor+Actor::YSpeed
    sta p2_actor+Actor::YFraction
    sta p2_actor+Actor::YSpeedFraction
    lda #2
    sta p2_actor+Actor::State
@done:
    rts

ground_partner:
    lda #1
    sta p2_grounded
    lda #0
    sta p2_actor+Actor::State
    sta p2_actor+Actor::YSpeed
    sta p2_actor+Actor::YFraction
    sta p2_actor+Actor::YSpeedFraction
    rts

; Platform objects share slots with enemies. The original engine advances
; them before this hook, so use their live positions for both riders.
is_platform:
    lda PAL_ENEMY_FLAGS,x
    beq @no
    lda PAL_ENEMY_IDS,x
    cmp #$24
    bcc @no
    cmp #$2D
    bcs @no
    lda PAL_ENEMY_Y_PAGE,x
    cmp #1
    bne @no
    sec
    rts
@no:
    clc
    rts

carry_partner:
    ldx p2_platform
    beq @done
    dex
    jsr is_platform
    bcc @detach
    lda PAL_ENEMY_X,x
    sec
    sbc p2_platform_x
    cmp #8
    bcc @carry
    cmp #$F9
    bcc @detach
@carry:
    sta p2_delta_x
    lda PAL_ENEMY_Y,x
    clc
    adc p2_platform_half
    sec
    sbc #$20
    bcc @detach
    cmp #$DB
    bcs @detach
    sta p2_y
    jmp walk_partner
@detach:
    lda #0
    sta p2_platform
@done:
    rts

land_on_platform:
    lda #0
    sta p2_platform
    lda p2_grounded
    bne @done
    lda p2_delta_y
    bmi @done
    ldx #5
@scan:
    jsr is_platform
    bcc @next
    txa
    asl
    asl
    tay
    jsr partner_horizontal_overlap
    bcc @next
    lda #0
    sta p2_platform_half
    jsr test_platform_height
    bcs @land
    lda PAL_ENEMY_IDS,x
    cmp #$2B
    bcc @next
    lda #$80                 ; Small lifts have a second platform 128px away.
    sta p2_platform_half
    jsr test_platform_height
    bcs @land
@next:
    dex
    bpl @scan
@done:
    rts
@land:
    sta p2_y
    lda PAL_ENEMY_X,x
    sta p2_platform_x
    inx
    stx p2_platform
    jmp ground_partner

test_platform_height:
    lda PAL_ENEMY_Y,x
    clc
    adc p2_platform_half
    sec
    sbc #$20
    bcc @miss
    cmp #$DB
    bcs @miss
    sta p2_new_y
    cmp p2_y
    beq @old_position
    bcs @miss
@old_position:
    clc
    adc #3
    cmp p2_previous_y
    bcc @miss
    lda p2_new_y
    sec
    rts
@miss:
    clc
    rts

; The native renderer has already calculated each visible segment's
; coordinates. Its next instruction is TYA, so leave X and Y untouched.
draw_firebar:
    jsr PAL_DRAW_FIREBAR
    lda p2_active
    beq @done
    jsr screen_position
    bne @done
    lda $06
    cmp #$F0
    bcs @done
    sec
    sbc p2_screen_x
    clc
    adc #7
    cmp #21
    bcs @done
    lda $07
    cmp #$F0
    bcs @done
    sec
    sbc p2_y
    clc
    adc #7
    cmp p2_top
    bcc @done
    cmp #39
    bcs @done
    lda #1
    sta p2_firebar_hit
@done:
    rts

probe_both_sides:
    sta probe_offset
    lda #2
    jsr probe_player_x
    bcs @solid
    lda #13
    jmp probe_player_x
@solid:
    rts

probe_player_x:
    clc
    adc p2_x
    sta probe_x
    lda p2_page
    adc #0
    sta probe_page
    lda probe_offset
    ; Fall through to the terrain lookup.

solid_tile_at_y:
    cmp #$20
    bcc @air
    cmp #$F0
    bcs @air
    and #$F0
    sec
    sbc #$20                 ; The first two tile rows belong to the status bar.
    tay
    lda probe_x
    lsr
    lsr
    lsr
    lsr
    sta terrain_pointer
    lda probe_page
    and #1
    beq @first_buffer
    lda terrain_pointer
    ora #$D0                 ; Second set of thirteen rows begins at $05D0.
    sta terrain_pointer
@first_buffer:
    lda #>PAL_TERRAIN
    sta terrain_pointer+1
    lda (terrain_pointer),y
    beq @air                 ; The original parser clears scenery to zero.
    cmp #$24                 ; Flagpole ball, shaft and vine.
    bcc @blocks
    cmp #$27
    bcc @air
@blocks:
    cmp #$5F
    beq @air
    cmp #$60
    beq @air
    cmp #$C2
    beq @air
    cmp #$C3
    beq @air
    sec
    rts
@air:
    clc
    rts

probe_body_centre:
    lda p2_y
    clc
    adc p2_top
    adc #6
    sta probe_offset
    lda #8
    jmp probe_player_x

update_vine_contact:
    jsr probe_body_centre
    cmp #$26
    bne @leave_vine
    lda p2_actor+Actor::State
    cmp #3
    beq @done
    lda p2_pad
    and #$08
    beq @done
    lda #3
    sta p2_actor+Actor::State
    lda #0
    sta p2_actor+Actor::XSpeed
    sta p2_actor+Actor::XFraction
    sta p2_platform
    rts
@leave_vine:
    lda p2_actor+Actor::State
    cmp #3
    bne @done
    lda #2
    sta p2_actor+Actor::State
@done:
    rts

; The stock game has one area and one scripted entrance/exit. A Luigi
; trigger hands the selected entrance to that same script for the team.
apply_partner_transition:
    jsr probe_body_centre
    cmp #$24
    beq @flag
    cmp #$25
    beq @flag
    cmp #$26
    bne @feet
    lda p2_actor+Actor::State
    cmp #3
    bne @feet
    lda p2_y
    cmp #$20
    bcs @feet
    lda p2_pad
    and #$08
    beq @feet
    jsr position_mario_for_transition
    lda #1
    sta PAL_GAME_ROUTINE
    sec
    rts
@flag:
    jsr position_mario_for_transition
    jsr PAL_FLAGPOLE
    sec
    rts
@feet:
    lda p2_grounded
    beq @stay
    lda p2_y
    clc
    adc #32
    sta probe_offset
    lda #3
    jsr probe_player_x
    cmp #$C5
    beq @axe
    sta $01
    lda #12
    jsr probe_player_x
    cmp #$C5
    beq @axe
    sta $00
    lda p2_pad
    and #4
    beq @check_side
    lda $01
    cmp #$10
    bne @check_side
    lda $00
    cmp #$11
    bne @check_side
    jsr position_mario_for_transition
    lda #4
    sta $0B
    jsr PAL_VERTICAL_PIPE
    sec
    rts
@check_side:
    lda p2_pad
    and #1
    beq @stay
    lda p2_y
    clc
    adc #24
    sta probe_offset
    lda #15
    jsr probe_player_x
    cmp #$6C
    beq @side
    cmp #$1F
    bne @stay
@side:
    jsr position_mario_for_transition
    lda #$85
    ldx PAL_CAMERA_PAGE
    beq @side_timer
    lda #$2B
@side_timer:
    sta PAL_CHANGE_AREA_TIMER
    jsr PAL_SIDE_PIPE
    sec
    rts
@axe:
    jsr position_mario_for_transition
    jsr set_tile_row
    jsr PAL_CASTLE_AXE
    sec
    rts
@stay:
    clc
    rts

position_mario_for_transition:
    lda p2_page
    sta PAL_P1_PAGE
    lda p2_x
    sta PAL_P1_X
    lda p2_y
    sta PAL_P1_Y
    lda #1
    sta PAL_P1_Y_PAGE
    lda #0
    sta PAL_P1_STATE
    sta PAL_P1_Y_SPEED
    sta $0416
    sta $0433
    rts

collect_terrain_coin:
    lda PAL_VRAM_OFFSET
    cmp #$18
    bcs @done
    jsr probe_body_centre
    cmp #$C2
    beq @collect
    cmp #$C3
    bne @done
@collect:
    jsr set_tile_row
    lda PAL_CURRENT_PLAYER
    pha
    lda PAL_PLAYER_COINS
    pha
    lda p2_coin_tally
    sta PAL_PLAYER_COINS
    lda #1
    sta PAL_CURRENT_PLAYER
    lda #$01
    sta PAL_SOUND_POWER_UP
    jsr PAL_COLLECT_COIN
    lda PAL_PLAYER_COINS
    sta p2_coin_tally
    pla
    sta PAL_PLAYER_COINS
    pla
    sta PAL_CURRENT_PLAYER
@done:
    rts

set_tile_row:
    lda probe_offset
    and #$F0
    sec
    sbc #$20
    sta $02
    rts

; Reuse the original block writer, replacement and item creation routines.
; The player coordinates are switched only for the duration of this call.
bump_block:
    sta p2_block_metatile
    lda PAL_AREA_TYPE
    beq @blocked
    lda PAL_BLOCK_TIMER
    bne @blocked
    lda PAL_VRAM_OFFSET
    cmp #$18
    bcs @blocked
    lda p2_block_metatile
    jsr PAL_SOLID_METATILE
    bcc @prepare
@blocked:
    rts
@prepare:
    jsr set_tile_row
    ldx #BlockActorCount-1
@load_actor:
    ldy block_actor_addresses,x
    lda $0700,y
    sta block_actor_saved,x
    lda block_actor_values,x
    tay
    lda $7000,y
    ldy block_actor_addresses,x
    sta $0700,y
    dex
    bpl @load_actor
    lda PAL_P1_PAGE
    pha
    lda PAL_P1_X
    pha
    lda PAL_P1_Y
    pha
    lda PAL_P1_Y_PAGE
    pha
    lda PAL_P1_Y_SPEED
    pha
    lda p2_x
    sta PAL_P1_X
    lda p2_page
    sta PAL_P1_PAGE
    lda p2_new_y
    sta PAL_P1_Y
    lda #1
    sta PAL_P1_Y_PAGE
    sta PAL_CURRENT_PLAYER
    lda p2_block_metatile
    jsr PAL_HEAD_COLLISION
    pla
    sta PAL_P1_Y_SPEED
    pla
    sta PAL_P1_Y_PAGE
    pla
    sta PAL_P1_Y
    pla
    sta PAL_P1_X
    pla
    sta PAL_P1_PAGE
    ldx #BlockActorCount-1
@restore_actor:
    ldy block_actor_addresses,x
    cpx #0
    bne @restore
    lda $0700,y
    sta p2_coin_tally
@restore:
    lda block_actor_saved,x
    sta $0700,y
    dex
    bpl @restore_actor
@done:
    rts

block_actor_addresses:
    .lobytes $075E, PAL_CURRENT_PLAYER, PAL_P1_SMALL, PAL_PLAYER_STATUS, PAL_CROUCHING
BlockActorCount = *-block_actor_addresses
block_actor_values:
    .lobytes p2_coin_tally, p2_status, p2_actor+Actor::Small, p2_status, p2_actor+Actor::Crouching

revive_mario_at_luigi:
    lda PAL_TIME_EXPIRED
    bne @done                ; Restart the area when the shared timer expires.
    lda p2_active
    beq @done
    lda p2_grounded
    beq @done                ; The original checkpoint is safer if both fell.
    jsr screen_position
    bne @done
    lda p2_page
    sta PAL_P1_PAGE
    lda p2_x
    sta PAL_P1_X
    lda p2_y
    sta PAL_P1_Y
    lda #0
    sta PAL_P1_STATE
    sta PAL_P1_X_SPEED
    sta PAL_P1_Y_SPEED
    sta $0400
    sta $0416
    sta $0433
    sta $06FF
    sta $0700
    sta $0705
    sta $0712                ; Clear the death-music latch.
    sta $0747                ; Clear the master timer hold.
    sta $FC
    lda #1
    sta PAL_P1_Y_PAGE
    sta PAL_P1_SMALL
    lda #0
    sta $0756                ; Respawn with the original small-player state.
    lda #48
    sta PAL_INJURY_TIMER
    lda #8
    sta PAL_GAME_ROUTINE
    jmp PAL_RESTORE_MUSIC
@done:
    rts

; Use the live box of the stock power-up in enemy slot five. Mario's
; ordinary collision pass already ran, so a pickup can only apply once.
collect_power_up:
    lda p2_star
    beq @check
    lda PAL_FRAME
    and #$0F
    bne @check
    dec p2_star
@check:
    lda PAL_ENEMY_FLAGS+5
    beq @done
    lda PAL_ENEMY_IDS+5
    cmp #$2E
    bne @done
    lda PAL_ENEMY_STATES+5
    cmp #6
    bcc @done
    lda PAL_ENEMY_Y_PAGE+5
    cmp #1
    bne @done
    ldy #5*4
    jsr partner_box_overlap
    bcc @done
    ldx #5
    jsr PAL_ERASE_ENEMY
    lda #$20
    sta PAL_SOUND_POWER_UP
    lda PAL_POWER_UP_TYPE
    cmp #3
    bcs @done                ; Unlimited lives already apply to either player.
    cmp #2
    bne @grow
    lda #$23
    sta p2_star
    bne @points
@grow:
    lda p2_status
    cmp #2
    bcs @points
    inc p2_status
    jsr set_partner_size
@points:
    ldx #2                   ; 1000 points, place 10^3 of the six score digits.
    jmp increment_luigi_score
@done:
    rts

set_partner_size:
    lda p2_status
    beq @small
    lda #0
    beq @set
@small:
    lda #1
    ldx #0
    stx p2_actor+Actor::Crouching
@set:
    sta p2_actor+Actor::Small
    jmp update_body_shape

; Initialise an unused projectile for the original fireball update next
; frame. Both actors use the hardware game's shared two-projectile pool.
throw_fireball:
    lda p2_fresh_spawn
    beq @check
    dec p2_fresh_spawn
    rts
@check:
    lda p2_status
    cmp #2
    bne @done
    lda p2_actor+Actor::Crouching
    bne @done
    lda p2_prev_ab
    eor #$FF
    and p2_pad
    and #$40
    beq @done
    ldx #0
    lda $24,x                ; Fireball state.
    beq @allocate
    inx
    lda $24,x
    bne @done
@allocate:
    lda p2_x
    clc
    adc #4
    sta $8D,x
    lda p2_page
    adc #0
    sta $74,x
    lda p2_y
    sta $D5,x
    lda #0
    sta $0407,x
    sta $041D,x
    sta $043A,x
    lda #1
    sta $BC,x
    sta $24,x
    lda #7
    sta $04A0,x
    lda #5                   ; PAL vertical fireball speed.
    sta $A6,x
    lda #$4C
    ldy p2_facing
    beq @set_speed
    lda #$B4
@set_speed:
    sta $5E,x
    lda #$20
    sta $FF
@done:
    rts

partner_horizontal_overlap:
    lda PAL_ENEMY_BOX,y
    cmp #$FF
    beq @miss
    lda p2_screen_x
    clc
    adc #13
    cmp PAL_ENEMY_BOX,y
    bcc @miss
    lda PAL_ENEMY_BOX+2,y
    sec
    sbc p2_screen_x
    bcc @miss
    cmp #2
    rts
@miss:
    clc
    rts

partner_box_overlap:
    jsr partner_horizontal_overlap
    bcc @miss
    lda p2_y
    clc
    adc p2_top
    sta p2_hit_top
    lda PAL_ENEMY_BOX+3,y
    cmp p2_hit_top
    bcc @miss
    lda p2_y
    clc
    adc #31
    cmp PAL_ENEMY_BOX+1,y
    rts
@miss:
    clc
    rts

; The base actor engine has already built screen-space hit boxes. Ignore
; scenery, platform and trigger slots, which have their own handling.
hit_enemies:
    lda p2_invincible
    beq @check
    dec p2_invincible
    rts
@check:
    lda p2_firebar_hit
    beq @start_enemies
    lda p2_star
    bne @start_enemies
    jmp hurt_partner
@start_enemies:
    ldx #5
@enemy:
    stx enemy_slot
    lda PAL_ENEMY_FLAGS,x
    beq @skip_inactive
    bmi @skip_inactive
    lda PAL_ENEMY_Y_PAGE,x
    cmp #1
    bne @skip_inactive
    lda PAL_ENEMY_IDS,x
    cmp #$16
    bcc @check_state
    cmp #$2D                 ; Bowser.
    beq @check_state
    cmp #$33                 ; Bullet Bill from a cannon.
    bne @skip_inactive
@check_state:
    lda PAL_ENEMY_STATES,x
    and #$20
    beq @bounds
@skip_inactive:
    jmp @next_enemy
@bounds:
    txa
    asl
    asl
    tay
    jsr partner_box_overlap
    bcc @skip_inactive
    lda p2_star
    beq @check_stomp
    lda PAL_ENEMY_IDS,x
    cmp #$15
    bcc @star_enemy
    rts
@star_enemy:
    lda #$20
    sta PAL_ENEMY_STATES,x
    ldx #3
    jmp increment_luigi_score
@touch:
    jmp hurt_partner
@check_stomp:
    lda PAL_AREA_TYPE
    beq @touch
    lda PAL_ENEMY_IDS,x
    cmp #$0C                 ; Lava bubble.
    beq @touch
    cmp #$0D                 ; Piranha plant.
    beq @touch
    cmp #$12                 ; Spiny.
    beq @touch
    cmp #$15
    bcs @touch
    lda PAL_ENEMY_STATES,x
    and #$87
    cmp #4
    bne @descending
    lda PAL_ENEMY_IDS,x
    cmp #5
    bcs @return              ; Already stomped Goomba.
    lda p2_screen_x
    cmp PAL_ENEMY_BOX,y
    lda #1
    ldy #$38
    bcc @kick
    lda #2
    ldy #$C8
@kick:
    sta PAL_ENEMY_DIRECTION,x
    tya
    sta PAL_ENEMY_X_SPEED,x
    lda #$84
    sta PAL_ENEMY_STATES,x
    lda #8
    sta p2_invincible
    rts
@descending:
    lda p2_delta_y
    beq @touch
    bmi @touch
    lda p2_previous_y
    clc
    adc #31
    cmp PAL_ENEMY_BOX+1,y
    bcs @touch
    lda PAL_ENEMY_IDS,x
    cmp #$0E
    bcc @ordinary_stomp
    cmp #$11
    bcs @ordinary_stomp
    and #1
    sta PAL_ENEMY_IDS,x
    lda #0
    beq @set_stomp_state
@ordinary_stomp:
    cmp #7
    lda #4
    bcc @set_stomp_state
    lda #$20                 ; A stomp on a non-shell enemy defeats it.
@set_stomp_state:
    sta PAL_ENEMY_STATES,x
    lda #$10
    sta PAL_ENEMY_TIMER,x
    lda #0
    sta PAL_ENEMY_X_SPEED,x
    sta p2_grounded
    lda #2
    sta p2_actor+Actor::State
    lda #$FD
    sta p2_actor+Actor::YSpeed
    lda #$04
    sta $FF                  ; Original stomp sound queue.
    ldx #3
    jmp increment_luigi_score
@next_enemy:
    ldx enemy_slot
    dex
    bmi @return
    jmp @enemy
@return:
    rts

hurt_partner:
    lda p2_status
    beq @lose_life
    lda #0
    sta p2_status
    lda #48
    sta p2_invincible
    jmp set_partner_size
@lose_life:
    jmp spawn_partner

increment_luigi_score:
@add_digit:
    inc PAL_LUIGI_SCORE,x
    lda PAL_LUIGI_SCORE,x
    cmp #10
    bcc @return
    lda #0
    sta PAL_LUIGI_SCORE,x
    dex
    bpl @add_digit
@return:
    rts

update_luigi_hud:
    lda PAL_VRAM_CONTROL
    bne @done                ; Let the original alternate buffer finish first.
    ldx PAL_VRAM_OFFSET
    cpx #$20                 ; All three commands fit before the next buffer.
    bcs @done
    ldy #0
@commands:
    lda luigi_hud_headers,y
    sta PAL_VRAM,x
    inx
    iny
    cpy #3
    bne @commands
    ldy #0
@palette:
    lda p2_status
    cmp #2
    bne @normal_color
    lda PAL_FIRE_COLORS,y
    bne @color
@normal_color:
    lda PAL_LUIGI_COLORS,y
@color:
    sta PAL_VRAM,x
    inx
    iny
    cpy #3
    bne @palette
    ldy #3
@hud:
    lda luigi_hud_headers,y
    sta PAL_VRAM,x
    inx
    iny
    cpy #luigi_hud_headers_end-luigi_hud_headers
    bne @hud
    ldy #0
@score:
    lda PAL_LUIGI_SCORE,y
    sta PAL_VRAM,x
    inx
    iny
    cpy #6
    bne @score
    lda #$20
    sta PAL_VRAM,x
    lda #$62
    sta PAL_VRAM+1,x
    lda #6
    sta PAL_VRAM+2,x
    inx
    inx
    inx
    ldy #0
@mario_score:
    lda PAL_MARIO_SCORE,y
    sta PAL_VRAM,x
    inx
    iny
    cpy #6
    bne @mario_score
    lda #0
    sta PAL_VRAM,x
    stx PAL_VRAM_OFFSET
@done:
    rts

luigi_hud_headers:
    .byte $3F, $15, 3          ; Sprite palette 1 (skip its universal entry).
    .byte $20, $4A, 5          ; Luigi label at the middle of the status bar.
    .byte $15, $1E, $12, $10, $12
    .byte $20, $6A, 6          ; Six Luigi digits in the former coin display.
luigi_hud_headers_end:

draw_partner:
    ; Use entries that the original renderer left hidden. Do not move sprite 0
    ; or overwrite any of P1's or the enemies' visible sprites.
    lda #4
    ldx p2_actor+Actor::Small
    bne @save_count
    lda #8
@save_count:
    sta p2_oam_count
    ldx #4
    ldy #0
@find_slot:
    lda PAL_OAM,x
    cmp #$F0
    bcc @next_slot
    txa
    sta p2_oam_slots,y
    iny
    cpy p2_oam_count
    beq @select_tiles
@next_slot:
    inx
    inx
    inx
    inx
    bne @find_slot
    rts
@select_tiles:
    lda p2_actor+Actor::Small
    bne @small_tiles
    lda p2_actor+Actor::Crouching
    beq @big_movement
    lda #$50
    bne @paint
@big_movement:
    lda p2_grounded
    bne @big_grounded
    lda PAL_SWIMMING
    beq @big_jump
    lda #$28
    bne @paint
@big_jump:
    lda #$20
    bne @paint
@big_grounded:
    lda p2_walking
    bne @big_walk
    lda #$C8
    bne @paint
@big_walk:
    lda PAL_FRAME
    and #8
    jmp @paint
@small_tiles:
    lda p2_grounded
    beq @jump_tiles
    lda p2_walking
    beq @idle_tiles
    lda PAL_FRAME
    and #4
    beq @first_walk_tiles
    lda #$6C
    bne @paint
@first_walk_tiles:
    lda #$64
    bne @paint
@jump_tiles:
    lda PAL_SWIMMING
    beq @short_jump
    lda #$8C
    bne @paint
@short_jump:
    lda #$84
    bne @paint
@idle_tiles:
    lda #$BC
@paint:
    sta p2_tiles
    ldy #0
@draw_tile:
    ldx p2_oam_slots,y
    lda p2_oam_count
    cmp #4
    bne @big_y
    lda p2_y
    clc
    adc #16
    bne @row
@big_y:
    lda p2_y
@row:
    clc
    adc tile_rows,y
    sec
    sbc #1
    sta PAL_OAM,x
    lda p2_screen_x
    clc
    adc tile_columns,y
    sta PAL_OAM+3,x
    lda p2_facing
    ora #1                   ; Second existing sprite palette distinguishes P2.
    sta PAL_OAM+2,x
    lda p2_facing
    beq @right_facing
    tya
    eor #1
    bpl @get_tile
@right_facing:
    tya
@get_tile:
    clc
    adc p2_tiles
    tax
    lda PAL_PLAYER_TILES,x
    ldx p2_oam_slots,y
    sta PAL_OAM+1,x
    iny
    cpy p2_oam_count
    bne @draw_tile
    rts

tile_rows:
    .byte 0, 0, 8, 8, 16, 16, 24, 24
tile_columns:
    .byte 0, 8, 0, 8, 0, 8, 0, 8
