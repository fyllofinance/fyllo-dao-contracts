# @version 0.2.12

"""
@notice MockCErc20 is only for test
"""

from vyper.interfaces import ERC20

implements: ERC20

interface Controller:
    def notifySavingsChange(addr: address):  nonpayable

event Transfer:
    _from: indexed(address)
    _to: indexed(address)
    _value: uint256

event Approval:
    _owner: indexed(address)
    _spender: indexed(address)
    _value: uint256

event ControllerChanged:
    _controller: address


name: public(String[64])
symbol: public(String[32])
decimals: public(uint256)

balanceOf: public(HashMap[address, uint256])
allowances: HashMap[address, HashMap[address, uint256]]
total_supply: uint256

underlying: public(address)

admin: public(address)
controller: public(address)

@external
def __init__(_name: String[64], _symbol: String[32], _decimals: uint256, _underlying: address):
    self.name = _name
    self.symbol = _symbol
    self.decimals = _decimals
    self.underlying = _underlying
    self.admin = msg.sender

@internal
def _mint(_to: address, _value: uint256):
    """
    @dev Mint an amount of the token and assigns it to an account.
         This encapsulates the modification of balances such that the
         proper events are emitted.
    @param _to The account that will receive the created tokens.
    @param _value The amount that will be created.
    """
    assert _to != ZERO_ADDRESS
    self.total_supply += _value
    self.balanceOf[_to] += _value
    log Transfer(ZERO_ADDRESS, _to, _value)


@internal
def _burn(_to: address, _value: uint256):
    """
    @dev Internal function that burns an amount of the token of a given
         account.
    @param _to The account whose tokens will be burned.
    @param _value The amount that will be burned.
    """
    assert _to != ZERO_ADDRESS
    self.total_supply -= _value
    self.balanceOf[_to] -= _value
    log Transfer(_to, ZERO_ADDRESS, _value)

@external
def deposit(_value: uint256):
    if _value > 0:
        ERC20(self.underlying).transferFrom(msg.sender, self, _value)
        self._mint(msg.sender, _value)
        if self.controller != ZERO_ADDRESS:
            Controller(self.controller).notifySavingsChange(msg.sender)

@external
def withdraw(_value: uint256):
    assert self.balanceOf[msg.sender] >= _value

    self._burn(msg.sender, _value)
    ERC20(self.underlying).transfer(msg.sender, _value)

    if self.controller != ZERO_ADDRESS:
        Controller(self.controller).notifySavingsChange(msg.sender)

@external
@view
def totalSupply() -> uint256:
    """
    @dev Total number of tokens in existence.
    """
    return self.total_supply


@external
@view
def allowance(_owner : address, _spender : address) -> uint256:
    """
    @dev Function to check the amount of tokens that an owner allowed to a spender.
    @param _owner The address which owns the funds.
    @param _spender The address which will spend the funds.
    @return An uint256 specifying the amount of tokens still available for the spender.
    """
    return self.allowances[_owner][_spender]


@external
def transfer(_to : address, _value : uint256) -> bool:
    """
    @dev Transfer token for a specified address
    @param _to The address to transfer to.
    @param _value The amount to be transferred.
    """
    # NOTE: vyper does not allow underflows
    #       so the following subtraction would revert on insufficient balance
    self.balanceOf[msg.sender] -= _value
    self.balanceOf[_to] += _value
    log Transfer(msg.sender, _to, _value)

    if self.controller != ZERO_ADDRESS:
        Controller(self.controller).notifySavingsChange(msg.sender)
        Controller(self.controller).notifySavingsChange(_to)

    return True


@external
def transferFrom(_from : address, _to : address, _value : uint256) -> bool:
    """
     @dev Transfer tokens from one address to another.
          Note that while this function emits a Transfer event, this is not required as per the specification,
          and other compliant implementations may not emit the event.
     @param _from address The address which you want to send tokens from
     @param _to address The address which you want to transfer to
     @param _value uint256 the amount of tokens to be transferred
    """
    # NOTE: vyper does not allow underflows
    #       so the following subtraction would revert on insufficient balance
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += _value
    self.allowances[_from][msg.sender] -= _value
    log Transfer(_from, _to, _value)

    if self.controller != ZERO_ADDRESS:
        Controller(self.controller).notifySavingsChange(_from)
        Controller(self.controller).notifySavingsChange(_to)

    return True


@external
def approve(_spender : address, _value : uint256) -> bool:
    """
    @dev Approve the passed address to spend the specified amount of tokens on behalf of msg.sender.
         Beware that changing an allowance with this method brings the risk that someone may use both the old
         and the new allowance by unfortunate transaction ordering. One possible solution to mitigate this
         race condition is to first reduce the spender's allowance to 0 and set the desired value afterwards:
         https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729
    @param _spender The address which will spend the funds.
    @param _value The amount of tokens to be spent.
    """
    assert _value == 0 or self.allowances[msg.sender][_spender] == 0
    self.allowances[msg.sender][_spender] = _value
    log Approval(msg.sender, _spender, _value)
    return True

@external
def setController(_controller: address):
    assert msg.sender == self.admin
    self.controller = _controller
    log ControllerChanged(_controller)
